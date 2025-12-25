# app/api/routers/invoices.py
"""
Module: Invoices (admin)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-31

Purpose:
    - Список счетов с фильтрами + пагинация
    - Карточка счета
    - Действия: выставить (ISSUED), отменить (CANCELED), выставить заново (REISSUE CANCELED→ISSUED)
    - Печатная версия (HTML)
    - Массовое выставление (по блоку / по всем)
    - Блок «Оплаты по счёту» (read-only) в карточке
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette import status

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import (
    User, RoleEnum, Block, Resident,
    Invoice, InvoiceStatus, InvoiceLine,
    Payment, PaymentApplication,  # <-- для блока оплат
)

router = APIRouter(prefix="/invoices", tags=["invoices"])
templates = Jinja2Templates(directory="app/templates")


def _see_other(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

# --- добавлено: мягкое приведение строкового query-параметра к int ---
def _to_int(val: str | None) -> int | None:
    if val is None:
        return None
    v = str(val).strip()
    if v == "":
        return None
    try:
        return int(v)
    except Exception:
        return None


def _apply_filters(
    db: Session,
    block_id: Optional[int],
    resident_id: Optional[int],
    status_val: Optional[str],
    year: Optional[int],
    month: Optional[int],
    q: Optional[str],
):
    """Единая сборка фильтров (для списка и JSON-хелпера)."""
    from sqlalchemy import or_
    query = db.query(Invoice).join(Resident, Resident.id == Invoice.resident_id)
    if block_id:
        query = query.filter(Resident.block_id == block_id)
    if resident_id:
        query = query.filter(Invoice.resident_id == resident_id)
    if status_val in {s.value for s in InvoiceStatus}:
        query = query.filter(Invoice.status == InvoiceStatus(status_val))
    if year:
        query = query.filter(Invoice.period_year == year)
    if month:
        query = query.filter(Invoice.period_month == month)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Invoice.number.ilike(like), Invoice.notes.ilike(like)))
    return query


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoices_list(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    block_id: str | None = None,
    resident_id: str | None = None,
    status_val: str | None = None,   # InvoiceStatus
    year: str | None = None,
    month: str | None = None,
    q: str | None = None,            # по номеру/примечанию
    page: int = 1,
    per_page: int = 25,
):
    # пустые строки → None, валидные строки → int
    block_id_i    = _to_int(block_id)
    resident_id_i = _to_int(resident_id)
    year_i        = _to_int(year)
    month_i       = _to_int(month)

    page = max(1, int(page or 1))
    per_page = int(per_page or 25)
    if per_page not in (25, 50, 100):
        per_page = 25

    query = _apply_filters(db, block_id_i, resident_id_i, status_val, year_i, month_i, q)

    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page

    items = (
        query
        .order_by(Invoice.period_year.desc(), Invoice.period_month.desc(), Invoice.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # --- оплачено / остаток по каждому счёту в выдаче ---
    ids = [inv.id for inv in items]
    paid_map = {}
    if ids:
        rows = (
            db.query(PaymentApplication.invoice_id, func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
            .filter(PaymentApplication.invoice_id.in_(ids))
            .group_by(PaymentApplication.invoice_id)
            .all()
        )
        paid_map = {inv_id: float(paid) for inv_id, paid in rows}
    
    # Проверяем и исправляем amount_total для каждого счета, если он не совпадает с суммой строк
    needs_commit = False
    for inv in items:
        lines_sum = db.query(
            func.coalesce(func.sum(InvoiceLine.amount_total), 0)
        ).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        
        if abs(float(inv.amount_total or 0) - float(lines_sum)) > 0.01:
            inv.amount_total = Decimal(str(lines_sum))
            net_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_net), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
            vat_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_vat), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
            inv.amount_net = Decimal(str(net_sum))
            inv.amount_vat = Decimal(str(vat_sum))
            needs_commit = True
    
    if needs_commit:
        db.commit()
    # -----------------------------------------------------

    residents = db.query(Resident).order_by(Resident.block_id.asc(), Resident.unit_number.asc()).all()
    blocks = db.query(Block).order_by(Block.name.asc()).all()

    # «лента» страниц
    window = 2
    pages = [p for p in range(max(1, page - window), min(last_page, page + window) + 1)]

    return templates.TemplateResponse("invoices.html", {
        "request": request,
        "user": user,
        "items": items,
        "residents": residents,
        "blocks": blocks,
        "InvoiceStatus": InvoiceStatus,
        # возвращаем исходные значения (строки), чтобы селекты/инпуты подсветились корректно
        "block_id": block_id or "",
        "resident_id": resident_id or "",
        "status_val": status_val or "",
        "year": year or "",
        "month": month or "",
        "q": q or "",
        # пагинация...
        "page": page, "per_page": per_page, "total": total, "last_page": last_page, "pages": pages,
        "per_page_options": [25, 50, 100],
        # карта «оплачено» по инвойсу
        "paid_map": paid_map,
    })


@router.get(
    "/ids",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoices_ids(
    db: Session = Depends(get_db),
    block_id: str | None = None,
    resident_id: str | None = None,
    status_val: str | None = None,
    year: str | None = None,
    month: str | None = None,
    q: str | None = None,
    limit: int = Query(default=1000, ge=1, le=10000, description="Лимит безопасности"),
):
    ids = [row.id for row in _apply_filters(
        db,
        _to_int(block_id),
        _to_int(resident_id),
        status_val,
        _to_int(year),
        _to_int(month),
        q,
    ).order_by(Invoice.id.asc()).limit(limit).all()]
    return {"ids": ids}


@router.post(
    "/bulk-issue",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoices_bulk_issue(
    db: Session = Depends(get_db),
    action: str = Form(...),               # 'by_block' | 'all'
    block_id: str | None = Form(None),     # может прийти "", парсим ниже
    due_date: str | None = Form(None),     # YYYY-MM-DD (необязательно)
):
    block_id_i = _to_int(block_id)
    if action == "by_block" and not block_id_i:
        return _see_other("/invoices?error=need_block")

    q = db.query(Invoice).join(Resident, Resident.id == Invoice.resident_id)\
                         .filter(Invoice.status == InvoiceStatus.DRAFT)
    if action == "by_block":
        q = q.filter(Resident.block_id == block_id_i)

    due: Optional[date] = None
    if due_date:
        try:
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
        except Exception:
            due = None

    cnt = 0
    for inv in q.all():
        if not inv.number:
            prefix = f"{inv.period_year}-{inv.period_month:02d}"
            last_num = (db.query(Invoice.number)
                          .filter(Invoice.period_year == inv.period_year,
                                  Invoice.period_month == inv.period_month,
                                  Invoice.number.ilike(f"{prefix}/%"))
                          .order_by(Invoice.number.desc())
                          .first())
            if last_num and last_num[0]:
                try:
                    seq = int(last_num[0].split("/")[-1]) + 1
                except Exception:
                    seq = inv.id
            else:
                seq = 1
            inv.number = f"{prefix}/{seq:06d}"

        inv.status = InvoiceStatus.ISSUED
        if due:
            inv.due_date = due
        cnt += 1

    db.commit()
    return _see_other(f"/invoices?ok=bulk_issued&cnt={cnt}")


@router.get(
    "/{invoice_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoice_detail(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return _see_other("/invoices?error=notfound")
    resident = db.get(Resident, inv.resident_id)

    # Проверяем и исправляем amount_total, если он не совпадает с суммой строк
    lines_sum = db.query(
        func.coalesce(func.sum(InvoiceLine.amount_total), 0)
    ).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
    
    if abs(float(inv.amount_total or 0) - float(lines_sum)) > 0.01:
        inv.amount_total = Decimal(str(lines_sum))
        net_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_net), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        vat_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_vat), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        inv.amount_net = Decimal(str(net_sum))
        inv.amount_vat = Decimal(str(vat_sum))
        db.commit()

    # ---- Блок «Оплаты по счёту» ----
    apps = (
        db.query(PaymentApplication)
          .join(Payment, Payment.id == PaymentApplication.payment_id)
          .filter(PaymentApplication.invoice_id == inv.id)
          .order_by(Payment.received_at.asc(), Payment.id.asc())
          .all()
    )
    paid_total = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                   .filter(PaymentApplication.invoice_id == inv.id).scalar()
    paid_total = paid_total or 0
    left_total = (inv.amount_total or 0) - paid_total

    return templates.TemplateResponse("invoice_detail.html", {
        "request": request,
        "user": user,
        "inv": inv,
        "resident": resident,
        "InvoiceStatus": InvoiceStatus,
        "apps": apps,
        "paid_total": paid_total,
        "left_total": left_total,
    })


@router.post(
    "/{invoice_id}/issue",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoice_issue(
    invoice_id: int,
    db: Session = Depends(get_db),
    number: str = Form(""),
    due_date: str = Form(""),
    notes: str = Form(""),
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return _see_other("/invoices?error=notfound")
    if inv.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELED):
        return _see_other(f"/invoices/{invoice_id}?error=immutable")

    inv.notes = (notes or "").strip() or None
    try:
        inv.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    except Exception:
        inv.due_date = None

    if not (number and number.strip()):
        if not inv.number:
            prefix = f"{inv.period_year}-{inv.period_month:02d}"
            last_num = (db.query(Invoice.number)
                          .filter(Invoice.period_year == inv.period_year,
                                  Invoice.period_month == inv.period_month,
                                  Invoice.number.ilike(f"{prefix}/%"))
                          .order_by(Invoice.number.desc()).first())
            if last_num and last_num[0]:
                try:
                    seq = int(last_num[0].split("/")[-1]) + 1
                except Exception:
                    seq = inv.id
            else:
                seq = 1
            inv.number = f"{prefix}/{seq:06d}"
    else:
        inv.number = number.strip()

    if inv.status == InvoiceStatus.DRAFT:
        inv.status = InvoiceStatus.ISSUED

    db.commit()
    return _see_other(f"/invoices/{invoice_id}?ok=issued")


@router.post(
    "/{invoice_id}/reissue",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoice_reissue(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    due_date: str = Form(""),
    comment: str = Form(""),
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return _see_other("/invoices?error=notfound")

    if inv.status != InvoiceStatus.CANCELED:
        return _see_other(f"/invoices/{invoice_id}?error=reissue_only_canceled")

    exists_active = db.query(Invoice.id).filter(
        Invoice.resident_id == inv.resident_id,
        Invoice.period_year == inv.period_year,
        Invoice.period_month == inv.period_month,
        Invoice.status != InvoiceStatus.CANCELED,
        Invoice.id != inv.id,
    ).first()
    if exists_active:
        return _see_other(f"/invoices/{invoice_id}?error=active_exists")

    try:
        inv.due_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else inv.due_date
    except Exception:
        pass

    if not inv.number:
        prefix = f"{inv.period_year}-{inv.period_month:02d}"
        last_num = (db.query(Invoice.number)
                      .filter(Invoice.period_year == inv.period_year,
                              Invoice.period_month == inv.period_month,
                              Invoice.number.ilike(f"{prefix}/%"))
                      .order_by(Invoice.number.desc()).first())
        if last_num and last_num[0]:
            try:
                seq = int(last_num[0].split("/")[-1]) + 1
            except Exception:
                seq = inv.id
        else:
            seq = 1
        inv.number = f"{prefix}/{seq:06d}"

    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    line = f"[REISSUED {stamp} by {user.username}] {comment}".strip()
    inv.notes = (inv.notes + "\n" + line) if inv.notes else line

    inv.status = InvoiceStatus.ISSUED
    db.commit()
    return _see_other(f"/invoices/{invoice_id}?ok=reissued")


@router.post(
    "/{invoice_id}/cancel",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def invoice_cancel(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    reason: str = Form(...),
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return _see_other("/invoices?error=notfound")

    if inv.status not in (InvoiceStatus.DRAFT, InvoiceStatus.ISSUED):
        return _see_other(f"/invoices/{invoice_id}?error=cancel_forbidden")

    reason = (reason or "").strip()
    if not reason:
        return _see_other(f"/invoices/{invoice_id}?error=empty_reason")

    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    audit_line = f"[CANCELED {stamp} by {user.username}] {reason}"
    inv.notes = f"{inv.notes}\n{audit_line}" if inv.notes else audit_line
    inv.status = InvoiceStatus.CANCELED
    db.commit()
    return _see_other(f"/invoices/{invoice_id}?ok=canceled")


@router.get(
    "/{invoice_id}/print",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def invoice_print(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return _see_other("/invoices?error=notfound")
    resident = db.get(Resident, inv.resident_id)
    return templates.TemplateResponse("invoice_pdf.html", {
        "request": request,
        "user": user,
        "inv": inv,
        "resident": resident,
    })
