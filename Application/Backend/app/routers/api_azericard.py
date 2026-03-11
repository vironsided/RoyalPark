from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Invoice, OnlineTransaction, Payment, PaymentLog, PaymentMethod, Resident
from ..utils import now_baku
from ..services.azericard import (
    CALLBACK_SIGN_FIELDS,
    CREATE_SIGN_FIELDS,
    amount_to_gateway,
    build_nonce,
    build_order_id,
    build_timestamp,
    generate_p_sign,
    verify_callback_signature,
)
from .api_payment_logic import apply_payment_to_invoice, apply_payment_to_invoices

router = APIRouter(prefix="/api/azericard", tags=["azericard-api"])


class InitiateRequest(BaseModel):
    resident_id: int
    amount: Decimal
    invoice_id: Optional[int] = None
    description: Optional[str] = None


class CompleteRequest(BaseModel):
    order_id: str
    amount: Decimal
    currency: str = "AZN"
    rrn: str
    int_ref: str


def _ensure_gateway_config() -> None:
    if not settings.AZERICARD_TERMINAL_ID:
        raise HTTPException(status_code=500, detail="AZERICARD_TERMINAL_ID is not configured")
    if not settings.AZERICARD_PRIVATE_KEY:
        raise HTTPException(status_code=500, detail="AZERICARD_PRIVATE_KEY is not configured")
    if not settings.AZERICARD_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="AZERICARD_PUBLIC_KEY is not configured")
    if not settings.AZERICARD_CALLBACK_URL:
        raise HTTPException(status_code=500, detail="AZERICARD_CALLBACK_URL is not configured")


def _ensure_signing_config() -> None:
    if not settings.AZERICARD_TERMINAL_ID:
        raise HTTPException(status_code=500, detail="AZERICARD_TERMINAL_ID is not configured")
    if not settings.AZERICARD_PRIVATE_KEY:
        raise HTTPException(status_code=500, detail="AZERICARD_PRIVATE_KEY is not configured")


def _pick(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        val = data.get(key)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return ""


def _wants_html(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    return "text/html" in accept or "*/*" in accept


@router.post("/initiate")
def initiate_payment(
    request: Request,
    payload: InitiateRequest,
    db: Session = Depends(get_db),
):
    _ensure_signing_config()

    resident = db.get(Resident, payload.resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    if payload.invoice_id:
        invoice = db.get(Invoice, payload.invoice_id)
        if not invoice or invoice.resident_id != payload.resident_id:
            raise HTTPException(status_code=400, detail="Invoice does not belong to resident")

    amount_str = amount_to_gateway(payload.amount)
    order_id = build_order_id(settings.AZERICARD_TERMINAL_ID)
    base_url = str(request.base_url).rstrip("/")
    success_url = settings.AZERICARD_SUCCESS_URL or f"{base_url}/api/azericard/success"
    fail_url = settings.AZERICARD_FAIL_URL or f"{base_url}/api/azericard/fail"

    req = {
        "AMOUNT": amount_str,
        "CURRENCY": settings.AZERICARD_CURRENCY,
        "ORDER": order_id,
        "DESC": (payload.description or f"Resident #{payload.resident_id}")[:250],
        "MERCH_NAME": settings.AZERICARD_MERCH_NAME,
        "MERCH_URL": settings.AZERICARD_MERCH_URL or settings.AZERICARD_CALLBACK_URL,
        "TERMINAL": settings.AZERICARD_TERMINAL_ID,
        "TRTYPE": "0",
        "TIMESTAMP": build_timestamp(),
        "NONCE": build_nonce(),
        "BACKREF": settings.AZERICARD_CALLBACK_URL,
    }
    req["MERCH_URL_OK"] = success_url
    req["MERCH_URL_FAIL"] = fail_url
    if settings.AZERICARD_LANG:
        req["LANG"] = settings.AZERICARD_LANG

    req["P_SIGN"] = generate_p_sign(req, CREATE_SIGN_FIELDS)

    tx = OnlineTransaction(
        resident_id=payload.resident_id,
        invoice_id=payload.invoice_id,
        order_id=order_id,
        amount_total=Decimal(amount_str),
        currency=req["CURRENCY"],
        trtype="0",
        gateway_status="INITIATED",
        request_payload=json.dumps(req, ensure_ascii=False),
    )
    db.add(tx)
    db.commit()

    return {
        "ok": True,
        "order_id": order_id,
        "gateway_url": settings.AZERICARD_GATEWAY_URL,
        "method": "POST",
        "params": req,
    }


@router.post("/callback")
async def azericard_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    _ensure_gateway_config()

    data: dict[str, str] = {}
    try:
        form = await request.form()
        data = {k: str(v) for k, v in form.items()}
    except Exception:
        data = {}
    if not data:
        try:
            body = await request.json()
            if isinstance(body, dict):
                data = {str(k): str(v) for k, v in body.items()}
        except Exception:
            data = {}
    order_id = _pick(data, "ORDER", "order")
    if not order_id:
        raise HTTPException(status_code=400, detail="ORDER is required")

    tx = db.query(OnlineTransaction).filter(OnlineTransaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Order not found")
    if tx.payment_id:
        return {"ok": True, "order_id": order_id, "payment_id": tx.payment_id, "status": "ALREADY_PROCESSED"}

    tx.callback_payload = json.dumps(data, ensure_ascii=False)
    tx.rrn = _pick(data, "RRN", "rrn")
    tx.int_ref = _pick(data, "INT_REF", "int_ref")
    tx.approval = _pick(data, "APPROVAL", "approval")
    tx.action_code = _pick(data, "ACTION", "action")
    tx.rc = _pick(data, "RC", "rc")
    tx.trtype = _pick(data, "TRTYPE", "trtype") or tx.trtype

    signature_ok = verify_callback_signature(data)
    action = _pick(data, "ACTION", "action")
    status_ok = action == "0"
    if not signature_ok:
        tx.gateway_status = "SIGNATURE_FAILED"
        db.commit()
        if _wants_html(request):
            return RedirectResponse(url=f"/api/azericard/fail?order_id={order_id}&reason=signature", status_code=302)
        raise HTTPException(status_code=400, detail="Invalid callback signature")

    if not status_ok:
        tx.gateway_status = "DECLINED"
        db.commit()
        if _wants_html(request):
            return RedirectResponse(url=f"/api/azericard/fail?order_id={order_id}&reason=declined", status_code=302)
        return {"ok": False, "order_id": order_id, "status": "DECLINED"}

    payment = Payment(
        resident_id=tx.resident_id,
        received_at=now_baku(),
        amount_total=tx.amount_total,
        method=PaymentMethod.ONLINE,
        reference=order_id,
        comment="AzeriCard online payment",
        created_by_id=None,
    )
    db.add(payment)
    db.flush()

    tx.payment_id = payment.id
    tx.gateway_status = "CONFIRMED"

    applied_amount = Decimal("0")
    if tx.invoice_id:
        applied_amount = apply_payment_to_invoice(
            db=db,
            payment_id=payment.id,
            invoice_id=tx.invoice_id,
            reference=f"AZERICARD:{order_id}",
        )
    apply_payment_to_invoices(
        db=db,
        payment_id=payment.id,
        resident_id=tx.resident_id,
        scope="all",
    )

    db.add(
        PaymentLog(
            payment_id=payment.id,
            resident_id=tx.resident_id,
            user_id=None,
            action="GATEWAY_CALLBACK",
            amount=float(tx.amount_total or 0),
            details=f"AzeriCard confirmed ORDER={order_id}; invoice_applied={float(applied_amount)}",
        )
    )
    db.commit()
    if _wants_html(request):
        return RedirectResponse(url=f"/api/azericard/success?order_id={order_id}", status_code=302)
    return {"ok": True, "order_id": order_id, "payment_id": payment.id}


@router.get("/status/{order_id}")
async def get_status(order_id: str, db: Session = Depends(get_db)):
    tx = db.query(OnlineTransaction).filter(OnlineTransaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_gateway_config()

    payload = {
        "ORDER": tx.order_id,
        "TERMINAL": settings.AZERICARD_TERMINAL_ID,
        "TRTYPE": "90",
        "TIMESTAMP": build_timestamp(),
        "NONCE": build_nonce(),
    }
    payload["P_SIGN"] = generate_p_sign(payload, ["ORDER", "TERMINAL", "TRTYPE", "TIMESTAMP", "NONCE"])

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(settings.AZERICARD_API_URL, data=payload)
    return {
        "ok": response.status_code == 200,
        "http_status": response.status_code,
        "gateway_response": response.text,
        "local_status": tx.gateway_status,
    }


@router.post("/complete")
async def complete_payment(payload: CompleteRequest):
    _ensure_gateway_config()
    req = {
        "ORDER": payload.order_id,
        "AMOUNT": amount_to_gateway(payload.amount),
        "CURRENCY": payload.currency,
        "RRN": payload.rrn,
        "INT_REF": payload.int_ref,
        "TERMINAL": settings.AZERICARD_TERMINAL_ID,
        "TRTYPE": "21",
        "TIMESTAMP": build_timestamp(),
        "NONCE": build_nonce(),
    }
    req["P_SIGN"] = generate_p_sign(req, CALLBACK_SIGN_FIELDS)

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(settings.AZERICARD_API_URL, data=req)
    return {"ok": response.status_code == 200, "http_status": response.status_code, "gateway_response": response.text}


@router.get("/success", response_class=HTMLResponse)
def payment_success_page(order_id: str | None = None):
    order_suffix = f"&order_id={order_id}" if order_id else ""
    return f"""
    <html><body style="font-family:Arial,sans-serif;padding:24px;">
      <h2>Payment successful</h2>
      <p>Your payment has been confirmed.</p>
      <a href="/resident/invoices?ok=online_payment_success{order_suffix}">Back to invoices</a>
    </body></html>
    """


@router.get("/fail", response_class=HTMLResponse)
def payment_fail_page(order_id: str | None = None):
    order_suffix = f"&order_id={order_id}" if order_id else ""
    return f"""
    <html><body style="font-family:Arial,sans-serif;padding:24px;">
      <h2>Payment failed</h2>
      <p>The payment was declined or canceled.</p>
      <a href="/resident/invoices?ok=online_payment_failed{order_suffix}">Back to invoices</a>
    </body></html>
    """
