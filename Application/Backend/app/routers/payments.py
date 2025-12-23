# app/api/routers/payments.py
"""
Module: Payments (admin)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-31

Purpose:
    - Список платежей + фильтры + пагинация
    - Создание платежа
    - Деталь платежа: автораспределение и ручное распределение по счетам
    - Пересчёт статусов счетов после распределения
    - Автораспределение аванса по всем открытым счетам резидента (FIFO)
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette import status

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import (
    User, RoleEnum,
    Resident, Invoice, InvoiceStatus,
    Payment, PaymentApplication, PaymentMethod,
    user_residents
)

router = APIRouter(prefix="/payments", tags=["payments"])
templates = Jinja2Templates(directory="app/templates")


def _see_other(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


# ---- мягкий парсер для пустых строк из query/form ----
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


# === helpers ===
def _recompute_invoice_status(db: Session, inv: Invoice):
    """Пересчитать статус счета по сумме применений."""
    paid = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
             .filter(PaymentApplication.invoice_id == inv.id).scalar() or Decimal("0")
    total = Decimal(inv.amount_total or 0)
    if paid <= 0:
        inv.status = inv.status if inv.status == InvoiceStatus.CANCELED else InvoiceStatus.ISSUED
    elif paid < total:
        inv.status = InvoiceStatus.PARTIAL
    elif paid == total:
        inv.status = InvoiceStatus.PAID
    else:
        inv.status = InvoiceStatus.OVERPAID


# =========================
#  Автораспределение аванса
# =========================
def auto_apply_advance(db: Session, resident_id: int) -> int:
    """
    Пробует автоматически применить свободные остатки платежей (авансы) пользователя
    ТОЛЬКО к открытым счетам (ISSUED/PARTIAL) КОНКРЕТНОГО резидента (resident_id).

    Деньги (аванс) берутся из ОБЩЕГО пула всех объектов этого пользователя.
    """
    affected_invoice_ids: set[int] = set()

    # 1) Находим все объекты (resident_id), привязанные к тем же пользователям, что и текущий дом
    linked_users_subquery = db.query(user_residents.c.user_id).filter(user_residents.c.resident_id == resident_id).subquery()
    associated_residents = db.query(user_residents.c.resident_id).filter(user_residents.c.user_id.in_(linked_users_subquery)).all()
    all_resident_ids = [r[0] for r in associated_residents]
    if not all_resident_ids:
        all_resident_ids = [resident_id]

    # 2) Открытые счета ТОЛЬКО ЦЕЛЕВОГО резидента (resident_id)
    # Это гарантирует, что аванс не уйдет на другой дом без команды пользователя
    open_invoices: list[Invoice] = (
        db.query(Invoice)
          .filter(Invoice.resident_id == resident_id,
                  Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]))
          .order_by(Invoice.period_year.asc(), Invoice.period_month.asc(), Invoice.id.asc())
          .all()
    )
    if not open_invoices:
        return 0

    # 3) Платежи со ВСЕХ объектов пользователя (общий пул аванса)
    payments: list[Payment] = (
        db.query(Payment)
          .filter(Payment.resident_id.in_(all_resident_ids))
          .order_by(Payment.received_at.asc(), Payment.id.asc())
          .all()
    )
    
    pay_leftover: dict[int, Decimal] = {}
    for p in payments:
        applied = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                    .filter(PaymentApplication.invoice_id == p.id).scalar() or Decimal("0")
        # Исправлено: суммируем применения к ЛЮБЫМ инвойсам, чтобы найти остаток платежа
        actual_applied = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                    .filter(PaymentApplication.payment_id == p.id).scalar() or Decimal("0")
        left = Decimal(p.amount_total or 0) - Decimal(actual_applied)
        if left > 0:
            pay_leftover[p.id] = left

    if not pay_leftover:
        return 0

    # 4) Проходим по счетам целевого дома и «доливаем» из общего пула авансов
    for inv in open_invoices:
        paid_all = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                     .filter(PaymentApplication.invoice_id == inv.id).scalar() or Decimal("0")
        inv_left = Decimal(inv.amount_total or 0) - Decimal(paid_all)
        if inv_left <= 0:
            continue

        for p in payments:
            if inv_left <= 0:
                break
            left = pay_leftover.get(p.id, Decimal("0"))
            if left <= 0:
                continue

            apply_amt = min(inv_left, left)
            if apply_amt <= 0:
                continue

            # найдём/создадим строку применения
            app = db.query(PaymentApplication).filter(
                PaymentApplication.payment_id == p.id,
                PaymentApplication.invoice_id == inv.id
            ).first()
            if app:
                app.amount_applied = Decimal(app.amount_applied or 0) + apply_amt
            else:
                db.add(PaymentApplication(payment_id=p.id, invoice_id=inv.id, amount_applied=apply_amt))

            db.flush() # фиксируем для корректного SUM в следующей итерации

            pay_leftover[p.id] = left - apply_amt
            inv_left -= apply_amt
            affected_invoice_ids.add(inv.id)

        _recompute_invoice_status(db, inv)

    return len(affected_invoice_ids)


# ======================
#         ROUTES
# ======================

@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payments_list(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    resident_id: str | None = None,   # ← принимаем как строку, парсим ниже
    method: str | None = None,        # PaymentMethod
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,             # reference/comment
    page: int = 1,
    per_page: int = 25,
):
    page = max(1, int(page or 1))
    per_page = int(per_page or 25)
    if per_page not in (25, 50, 100):
        per_page = 25

    resident_id_i = _to_int(resident_id)

    query = db.query(Payment).join(Resident, Resident.id == Payment.resident_id)

    if resident_id_i:
        query = query.filter(Payment.resident_id == resident_id_i)
    if method in {m.value for m in PaymentMethod}:
        query = query.filter(Payment.method == PaymentMethod(method))
    if date_from:
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Payment.received_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Payment.received_at <= dt)
        except Exception:
            pass
    if q:
        like = f"%{q.strip()}%"
        query = query.filter((Payment.reference.ilike(like)) | (Payment.comment.ilike(like)))

    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page

    items = query.order_by(Payment.received_at.desc(), Payment.id.desc()) \
                 .offset((page - 1) * per_page).limit(per_page).all()

    residents = db.query(Resident).order_by(Resident.block_id.asc(), Resident.unit_number.asc()).all()

    pages = [p for p in range(max(1, page - 2), min(last_page, page + 2) + 1)]
    return templates.TemplateResponse("payments.html", {
        "request": request, "user": user,
        "items": items, "residents": residents,
        "PaymentMethod": PaymentMethod,
        "resident_id": resident_id or "", "method": method or "",
        "date_from": date_from or "", "date_to": date_to or "", "q": q or "",
        "page": page, "per_page": per_page, "last_page": last_page, "total": total, "pages": pages,
        "per_page_options": [25, 50, 100],
    })


@router.get(
    "/create",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payment_create_form(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    residents = db.query(Resident).order_by(Resident.block_id.asc(), Resident.unit_number.asc()).all()
    return templates.TemplateResponse("payment_form.html", {
        "request": request, "user": user, "residents": residents, "PaymentMethod": PaymentMethod,
    })


@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payment_create(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
    received_at: str = Form(...),
    amount_total: Decimal = Form(...),
    method: str = Form(...),
    reference: str = Form(""),
    comment: str = Form(""),
):
    try:
        rcv = datetime.strptime(received_at, "%Y-%m-%d").date()
    except Exception:
        rcv = datetime.utcnow().date()

    if method not in {m.value for m in PaymentMethod}:
        return _see_other("/payments?error=bad_method")

    p = Payment(
        resident_id=resident_id,
        received_at=rcv,
        amount_total=Decimal(amount_total),
        method=PaymentMethod(method),
        reference=(reference or None),
        comment=(comment or None),
        created_by_id=user.id,
    )
    db.add(p)
    db.commit()  # сначала фиксируем сам платеж, чтобы он появился в расчёте аванса

    # --- НОВОЕ: сразу дольём аванс в открытые счета ---
    auto_apply_advance(db, resident_id)
    db.commit()

    return _see_other(f"/payments/{p.id}?ok=created")


@router.get(
    "/{payment_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payment_detail(
    payment_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.get(Payment, payment_id)
    if not p:
        return _see_other("/payments?error=notfound")

    # открытые счета резидента (ISSUED/PARTIAL), FIFO по периоду
    open_invoices = db.query(Invoice) \
        .filter(Invoice.resident_id == p.resident_id,
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL])) \
        .order_by(Invoice.period_year.asc(), Invoice.period_month.asc(), Invoice.id.asc()) \
        .all()

    # остаток к оплате по счету = total - paid
    def invoice_left(inv: Invoice) -> Decimal:
        paid = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                 .filter(PaymentApplication.invoice_id == inv.id).scalar() or Decimal("0")
        return Decimal(inv.amount_total or 0) - paid

    open_invoices_view = [{"inv": inv, "left": invoice_left(inv)} for inv in open_invoices]

    return templates.TemplateResponse("payment_detail.html", {
        "request": request, "user": user,
        "p": p, "open_invoices": open_invoices_view,
    })


@router.post(
    "/{payment_id}/auto-apply",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payment_auto_apply(
    payment_id: int,
    db: Session = Depends(get_db),
):
    p = db.get(Payment, payment_id)
    if not p:
        return JSONResponse({"ok": False, "error": "notfound"}, status_code=404)

    # пытаемся разложить только остаток ЭТОГО платежа на открытые счета
    # (локальная версия FIFO для одного платежа)
    leftover = Decimal(p.amount_total or 0) - (
        db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
          .filter(PaymentApplication.payment_id == p.id).scalar() or Decimal("0")
    )
    plan: list[dict] = []
    if leftover <= 0:
        return {"ok": True, "plan": plan}

    open_invoices = db.query(Invoice) \
        .filter(Invoice.resident_id == p.resident_id,
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL])) \
        .order_by(Invoice.period_year.asc(), Invoice.period_month.asc(), Invoice.id.asc()) \
        .all()

    for inv in open_invoices:
        paid = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                 .filter(PaymentApplication.invoice_id == inv.id).scalar() or Decimal("0")
        left = Decimal(inv.amount_total or 0) - paid
        if left <= 0:
            continue
        apply_amt = min(leftover, left)
        if apply_amt > 0:
            plan.append({"invoice_id": inv.id, "amount": float(apply_amt)})
            leftover -= apply_amt
            if leftover <= 0:
                break

    return {"ok": True, "plan": plan, "left_after": float(leftover)}


@router.post(
    "/{payment_id}/applications",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def payment_save_applications(
    payment_id: int,
    db: Session = Depends(get_db),
    data_json: str = Form(...),  # [{"invoice_id": 10, "amount": 50.00}, ...]
):
    """
    Умное слияние:
    - существующие применения НЕ удаляем;
    - для счетов, пришедших в payload, создаём/обновляем сумму;
    - остальные оставляем как есть.
    """
    p = db.get(Payment, payment_id)
    if not p:
        return _see_other("/payments?error=notfound")

    try:
        import json
        items = json.loads(data_json)
        assert isinstance(items, list)
    except Exception:
        return _see_other(f"/payments/{payment_id}?error=bad_payload")

    # Текущие применения этого платежа: invoice_id -> Decimal(amount)
    cur_apps = {
        a.invoice_id: Decimal(a.amount_applied or 0)
        for a in db.query(PaymentApplication).filter(PaymentApplication.payment_id == p.id).all()
    }

    # Построим целевые значения после сохранения: начнём с текущих
    target_apps = dict(cur_apps)

    # Валидации по каждому переданному элементу и установка целевого значения
    for it in items:
        inv_id = int(it["invoice_id"])
        amt_new = Decimal(str(it["amount"]))
        if amt_new <= 0:
            # нулевую строку пока трактуем как "пропущено" (не удаляем)
            continue

        inv = db.get(Invoice, inv_id)
        if not inv:
            return _see_other(f"/payments/{payment_id}?error=bad_invoice")
            
        # Проверяем, что счет и платеж принадлежат одному и тому же пользователю (или пользователям)
        payment_users = db.query(user_residents.c.user_id).filter(user_residents.c.resident_id == p.resident_id).all()
        invoice_users = db.query(user_residents.c.user_id).filter(user_residents.c.resident_id == inv.resident_id).all()
        
        p_user_ids = {u[0] for u in payment_users}
        i_user_ids = {u[0] for u in invoice_users}
        
        # Если есть хотя бы один общий пользователь, разрешаем применение
        # Также разрешаем, если resident_id совпадает (на случай если пользователь не привязан)
        if not (p_user_ids & i_user_ids) and inv.resident_id != p.resident_id:
            return _see_other(f"/payments/{payment_id}?error=bad_invoice_owner")

        # Остаток по счёту на сейчас (с учётом ВСЕХ платежей)
        paid_all = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0)) \
                     .filter(PaymentApplication.invoice_id == inv.id).scalar() or Decimal("0")
        left_now = Decimal(inv.amount_total or 0) - Decimal(paid_all)
        if left_now < 0:
            left_now = Decimal("0")

        # Сколько уже применено ИМЕННО этим платежом к этому счёту
        cur_amt_this = cur_apps.get(inv_id, Decimal("0"))

        # Разрешённый верхний предел для нового целевого значения:
        # можно занять весь текущий остаток, плюс та сумма, которую этот платёж уже занимал ранее
        allowed_max = left_now + cur_amt_this
        if amt_new > allowed_max:
            return _see_other(f"/payments/{payment_id}?error=too_much_for_invoice")

        target_apps[inv_id] = amt_new  # обновляем/ставим целевое значение

    # Проверка лимита по сумме платежа:
    total_target = sum(target_apps.values(), Decimal("0"))
    if total_target > Decimal(p.amount_total or 0):
        return _see_other(f"/payments/{payment_id}?error=too_much_for_payment")

    # Применяем изменения: обновляем существующие, создаём недостающие
    # (не пришедшие в payload оставляем как есть)
    for inv_id, tgt in target_apps.items():
        app = db.query(PaymentApplication).filter(
            PaymentApplication.payment_id == p.id,
            PaymentApplication.invoice_id == inv_id
        ).first()
        if app:
            app.amount_applied = tgt
        else:
            db.add(PaymentApplication(payment_id=p.id, invoice_id=inv_id, amount_applied=tgt))

    db.flush()

    # Пересчитать статусы вовлечённых счетов
    inv_ids = list(target_apps.keys())
    invs = db.query(Invoice).filter(Invoice.id.in_(inv_ids)).all()
    for inv in invs:
        _recompute_invoice_status(db, inv)

    db.commit()
    return _see_other(f"/payments/{payment_id}?ok=saved")
