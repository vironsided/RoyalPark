# app/api/routers/resident_portal.py
"""
Module: Resident Portal (Личный кабинет жителя)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz

Purpose:
    - Вход/выход жителя
    - Главная ЛК (дашборд с корректными суммами: за месяц, долг по счетам, аванс, к оплате)
    - Профиль / смена пароля / аватар
    - Детализация по дому (история показаний) с умными фильтрами периода
    - Мои счета (список / деталь)
    - Сообщить об оплате (создание Payment со ссылкой на резидента)
    - Погасить из аванса (ручной запуск авторазмещения аванса по открытым счетам)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
from decimal import Decimal
import pathlib

from ..database import get_db
from ..models import (
    User, RoleEnum,
    Invoice, InvoiceStatus, InvoiceLine,
    Resident, ResidentMeter, MeterReading, MeterType,
    Payment, PaymentApplication, PaymentMethod,
    Notification, NotificationStatus,
)
from ..utils import now_baku, to_baku_datetime
from ..security import (
    verify_password, set_session, clear_session, hash_password, get_user_id_from_session
)
# НОВОЕ: сервис автораскладки аванса
from .payments import auto_apply_advance

router = APIRouter(prefix="/resident", tags=["resident"])
templates = Jinja2Templates(directory="app/templates")


def _get_resident_user(request: Request, db: Session) -> User | None:
    uid = get_user_id_from_session(request)
    if not uid:
        return None
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return None
    return user


# ---------------------- Login / Logout ----------------------

@router.get("/login", response_class=HTMLResponse)
def resident_login_form(request: Request):
    return templates.TemplateResponse("resident_login.html", {"request": request, "error": None})


@router.post("/login")
def resident_login(request: Request, db: Session = Depends(get_db),
                   username: str = Form(...), password: str = Form(...)):
    user = (
        db.query(User)
          .filter(User.username == username, User.role == RoleEnum.RESIDENT)
          .first()
    )
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        return templates.TemplateResponse(
            "resident_login.html",
            {"request": request, "error": "Неверные учетные данные"},
            status_code=400,
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    resp = RedirectResponse(url="/resident", status_code=302)
    set_session(resp, user.id)
    if user.require_password_change:
        resp = RedirectResponse(url="/force-change-password", status_code=302)
        set_session(resp, user.id)
    return resp


@router.get("/logout")
def resident_logout():
    resp = RedirectResponse(url="/resident/login", status_code=302)
    clear_session(resp)
    return resp


# ---------------------- Dashboard ----------------------

@router.get("/", response_class=HTMLResponse)
def resident_home(request: Request, db: Session = Depends(get_db)):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    residents = user.resident_links or []
    today = datetime.utcnow().date()
    cur_y, cur_m = today.year, today.month

    # Для каждого дома: за месяц, долг, аванс, к оплате, due по текущему счёту,
    # а также month_total/month_paid для прогресса за месяц.
    month_due: dict[int, Decimal]      = {}
    month_total: dict[int, Decimal]    = {}
    month_paid: dict[int, Decimal]     = {}
    debt_total: dict[int, Decimal]     = {}
    advance_total: dict[int, Decimal]  = {}
    pay_now: dict[int, Decimal]        = {}
    due_info: dict[int, dict]          = {}  # {rid: {"due_date": date|None, "state": "ok|soon|over|none"}}

    for r in residents:
        # ---- Счёт текущего месяца (живой) и остаток по нему ----
        inv_month = (
            db.query(Invoice)
              .filter(Invoice.resident_id == r.id,
                      Invoice.period_year == cur_y,
                      Invoice.period_month == cur_m,
                      Invoice.status != InvoiceStatus.CANCELED)
              .first()
        )
        if inv_month:
            paid_m = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                       .filter(PaymentApplication.invoice_id == inv_month.id).scalar() or 0
            md = Decimal(inv_month.amount_total or 0) - Decimal(paid_m)
            month_due[r.id]   = md if md > 0 else Decimal("0")
            month_total[r.id] = Decimal(inv_month.amount_total or 0)
            month_paid[r.id]  = Decimal(paid_m)

            due = inv_month.due_date
            state = "none"
            if due:
                days = (due - today).days
                if days < 0:
                    state = "over"
                elif days <= 3:
                    state = "soon"
                else:
                    state = "ok"
            due_info[r.id] = {"due_date": due, "state": state}
        else:
            month_due[r.id]   = Decimal("0")
            month_total[r.id] = Decimal("0")
            month_paid[r.id]  = Decimal("0")
            due_info[r.id]    = {"due_date": None, "state": "none"}

        # ---- Общий долг по всем живым счетам ----
        inv_total = db.query(func.coalesce(func.sum(Invoice.amount_total), 0))\
                      .filter(Invoice.resident_id == r.id,
                              Invoice.status != InvoiceStatus.CANCELED).scalar() or 0
        paid_total = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                       .join(Invoice, Invoice.id == PaymentApplication.invoice_id)\
                       .filter(Invoice.resident_id == r.id,
                               Invoice.status != InvoiceStatus.CANCELED).scalar() or 0
        debt = Decimal(inv_total) - Decimal(paid_total)
        debt_total[r.id] = debt if debt > 0 else Decimal("0")

        # ---- Аванс (свободный остаток всех платежей) ----
        pay_sum = db.query(func.coalesce(func.sum(Payment.amount_total), 0))\
                    .filter(Payment.resident_id == r.id).scalar() or 0
        appl_sum = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                     .join(Payment, Payment.id == PaymentApplication.payment_id)\
                     .filter(Payment.resident_id == r.id).scalar() or 0
        adv = Decimal(pay_sum) - Decimal(appl_sum)
        advance_total[r.id] = adv if adv > 0 else Decimal("0")

        # ---- К оплате сейчас = долг - аванс (минимум 0) ----
        pay_now[r.id] = max(debt_total[r.id] - advance_total[r.id], Decimal("0"))

    # Сводка по всем домам
    total_month = sum(month_due.values(), Decimal("0"))
    total_debt  = sum(debt_total.values(), Decimal("0"))
    total_adv   = sum(advance_total.values(), Decimal("0"))
    total_pay   = sum(pay_now.values(), Decimal("0"))

    return templates.TemplateResponse("resident_dashboard.html", {
        "request": request,
        "user": user,
        "residents": residents,
        "month_due": month_due,
        "month_total": month_total,
        "month_paid": month_paid,
        "debt_total": debt_total,
        "advance_total": advance_total,
        "pay_now": pay_now,
        "due_info": due_info,
        "total_month": total_month,
        "total_debt": total_debt,
        "total_adv": total_adv,
        "total_pay": total_pay,
    })


# ---------------------- Профиль ----------------------

def _save_avatar(file: UploadFile, user_id: int) -> str | None:
    if not file:
        return None
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        return None
    ext = ".jpg" if file.content_type == "image/jpeg" else (".png" if file.content_type == "image/png" else ".webp")
    base_dir = pathlib.Path("uploads/avatars") / str(user_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"avatar{ext}"
    with open(path, "wb") as f:
        f.write(file.file.read())
    rel_path = f"/uploads/avatars/{user_id}/avatar{ext}"
    return rel_path


@router.post("/profile/update")
def resident_profile_update(
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    avatar: UploadFile = File(None),
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    user.full_name = full_name or None
    user.phone = phone or None
    user.email = email or None

    if avatar and avatar.filename:
        rel = _save_avatar(avatar, user.id)
        if rel:
            user.avatar_path = rel

    db.commit()
    return RedirectResponse(url="/resident?ok=profile_saved", status_code=302)


@router.post("/profile/change-password")
def resident_change_password(
    request: Request,
    db: Session = Depends(get_db),
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    if new_password != new_password2:
        return RedirectResponse(url="/resident?error=pw_mismatch", status_code=302)
    if not verify_password(current_password, user.password_hash):
        return RedirectResponse(url="/resident?error=pw_wrong", status_code=302)
    if len(new_password) < 6:
        return RedirectResponse(url="/resident?error=pw_short", status_code=302)

    user.password_hash = hash_password(new_password)
    user.require_password_change = False
    user.temp_password_plain = None
    user.last_password_change_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/resident?ok=password_changed", status_code=302)


# ---------------------- Обращения жителя ----------------------


@router.get("/notifications", response_class=HTMLResponse)
def resident_notifications_form(
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_resident_user(request, db)
    if not user:
        return RedirectResponse(url="/resident/login", status_code=302)

    residents = user.resident_links or []
    from sqlalchemy import or_
    recent = (
        db.query(Notification)
        .filter(
            Notification.user_id == user.id,
            or_(
                Notification.notification_type == "APPEAL",
                Notification.notification_type == None
            )
        )
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )

    return templates.TemplateResponse(
        "resident_notification_form.html",
        {
            "request": request,
            "user": user,
            "residents": residents,
            "notifications": recent,
            "NotificationStatus": NotificationStatus,
        },
    )


@router.post("/notifications")
def resident_notifications_submit(
    request: Request,
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
    message: str = Form(...),
):
    user = _get_resident_user(request, db)
    if not user:
        return RedirectResponse(url="/resident/login", status_code=302)

    message = (message or "").strip()
    if len(message) < 5:
        return RedirectResponse(url="/resident/notifications?error=message_short", status_code=302)

    resident = db.get(Resident, resident_id)
    if not resident or resident not in (user.resident_links or []):
        return RedirectResponse(url="/resident/notifications?error=bad_resident", status_code=302)

    notif = Notification(
        user_id=user.id,
        resident_id=resident.id,
        message=message,
        status=NotificationStatus.UNREAD,
        notification_type="APPEAL",
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()

    return RedirectResponse(url="/resident/notifications?ok=notification_sent", status_code=302)


@router.post("/notifications/{notification_id}/update")
def resident_notifications_update(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    message: str = Form(...),
):
    user = _get_resident_user(request, db)
    if not user:
        return RedirectResponse(url="/resident/login", status_code=302)

    notif = db.get(Notification, notification_id)
    if not notif or notif.user_id != user.id:
        return RedirectResponse(url="/resident/notifications?error=notfound", status_code=302)

    if notif.status != NotificationStatus.UNREAD:
        return RedirectResponse(url="/resident/notifications?error=edit_forbidden", status_code=302)

    message = (message or "").strip()
    if len(message) < 5:
        return RedirectResponse(url=f"/resident/notifications?error=message_short", status_code=302)

    notif.message = message
    db.commit()

    return RedirectResponse(url="/resident/notifications?ok=notification_updated", status_code=302)


@router.post("/notifications/{notification_id}/delete")
def resident_notifications_delete(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = _get_resident_user(request, db)
    if not user:
        return RedirectResponse(url="/resident/login", status_code=302)

    notif = db.get(Notification, notification_id)
    if not notif or notif.user_id != user.id:
        return RedirectResponse(url="/resident/notifications?error=notfound", status_code=302)

    db.delete(notif)
    db.commit()
    return RedirectResponse(url="/resident/notifications?ok=notification_deleted", status_code=302)


# ---------------------- Детализация по дому (фильтры периода) ----------------------

@router.get("/detail/{resident_id}", response_class=HTMLResponse)
def resident_detail(
    resident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    from_: str | None = None,   # YYYY-MM-DD
    to: str | None = None,      # YYYY-MM-DD
    range_: str | None = None,  # 'month' | '3m' | '6m' | 'year'
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    r = db.get(Resident, resident_id)
    if not r or (r not in (user.resident_links or [])):
        return RedirectResponse(url="/resident?error=forbidden", status_code=302)

    start_dt: datetime | None = None
    end_dt: datetime | None = None
    today = datetime.utcnow().date()

    if range_ in {"month", "3m", "6m", "year"}:
        if range_ == "month":
            start_dt = datetime(today.year, today.month, 1)
            end_dt = datetime(
                today.year + (1 if today.month == 12 else 0),
                (1 if today.month == 12 else today.month + 1),
                1
            )
        elif range_ == "3m":
            m = today.month - 2
            y = today.year
            while m <= 0:
                m += 12; y -= 1
            start_dt = datetime(y, m, 1)
            end_dt = datetime(
                today.year + (1 if today.month == 12 else 0),
                (1 if today.month == 12 else today.month + 1),
                1
            )
        elif range_ == "6m":
            m = today.month - 5
            y = today.year
            while m <= 0:
                m += 12; y -= 1
            start_dt = datetime(y, m, 1)
            end_dt = datetime(
                today.year + (1 if today.month == 12 else 0),
                (1 if today.month == 12 else today.month + 1),
                1
            )
        elif range_ == "year":
            m = today.month - 11
            y = today.year
            while m <= 0:
                m += 12; y -= 1
            start_dt = datetime(y, m, 1)
            end_dt = datetime(
                today.year + (1 if today.month == 12 else 0),
                (1 if today.month == 12 else today.month + 1),
                1
            )

    if start_dt is None and end_dt is None and (from_ or to):
        try:
            if from_:
                y, m, d = map(int, from_.split("-"))
                start_dt = datetime(y, m, d)
            if to:
                y2, m2, d2 = map(int, to.split("-"))
                end_dt = datetime(y2, m2, d2) + timedelta(days=1)
        except Exception:
            start_dt, end_dt = None, None

    history: dict[int, list[MeterReading]] = {}
    for m in r.meters:
        q = db.query(MeterReading).filter(MeterReading.resident_meter_id == m.id)
        if start_dt is not None:
            q = q.filter(MeterReading.reading_date >= start_dt)
        if end_dt is not None:
            q = q.filter(MeterReading.reading_date < end_dt)
        recs = q.order_by(MeterReading.reading_date.desc(), MeterReading.id.desc()).all()
        history[m.id] = recs

    from_val = start_dt.strftime("%Y-%m-%d") if start_dt else ""
    to_val = (end_dt - timedelta(days=1)).strftime("%Y-%m-%d") if end_dt else ""

    return templates.TemplateResponse("resident_detail.html", {
        "request": request,
        "user": user,
        "resident": r,
        "meters": r.meters,
        "history": history,
        "MeterType": MeterType,
        "from_val": from_val,
        "to_val": to_val,
        "range_val": range_ or "",
    })


# ---------------------- Мои счета (список) ----------------------

@router.get("/invoices", response_class=HTMLResponse)
def resident_invoices(
    request: Request,
    db: Session = Depends(get_db),
    status_val: str | None = None,
    resident_id: str | None = None,
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    resident_ids = [r.id for r in (user.resident_links or [])]
    q = db.query(Invoice).filter(Invoice.resident_id.in_(resident_ids))
    if resident_id and resident_id.strip().isdigit():
        rid = int(resident_id)
        if rid in resident_ids:
            q = q.filter(Invoice.resident_id == rid)
    if status_val in {s.value for s in InvoiceStatus}:
        q = q.filter(Invoice.status == InvoiceStatus(status_val))
    items = q.order_by(Invoice.period_year.desc(), Invoice.period_month.desc(), Invoice.id.desc()).all()

    paid_map = {}
    if items:
        ids = [inv.id for inv in items]
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

       # --- диапазон дат "предыдущее показание - текущее" по каждой квитанции ---
    period_map: dict[int, dict[str, str | None]] = {}
    if items:
        ids = [inv.id for inv in items]

    # подзапрос: для каждого показания находим предыдущее по этому же счётчику
    mr_with_prev = (
        db.query(
            MeterReading.id.label("mr_id"),
            MeterReading.resident_meter_id.label("meter_id"),
            MeterReading.reading_date.label("curr_dt"),
            func.lag(MeterReading.reading_date)
                .over(
                    partition_by=MeterReading.resident_meter_id,
                    order_by=MeterReading.reading_date
                )
                .label("prev_dt"),
        )
        .subquery("mr_with_prev")
    )

    rows = (
        db.query(
            Invoice.id.label("inv_id"),
            func.min(mr_with_prev.c.prev_dt).label("min_prev"),
            func.max(mr_with_prev.c.curr_dt).label("max_curr"),
        )
        .join(InvoiceLine, InvoiceLine.invoice_id == Invoice.id)
        .join(mr_with_prev, mr_with_prev.c.mr_id == InvoiceLine.meter_reading_id)
        .filter(Invoice.id.in_(ids))
        .group_by(Invoice.id)
        .all()
    )

    for r in rows:
        end_dt = r.max_curr
        if not end_dt:
            continue

        end_str = end_dt.date().strftime('%d.%m.%Y')
        start_dt = r.min_prev
        start_str = start_dt.date().strftime('%d.%m.%Y') if start_dt else None

        period_map[r.inv_id] = {
            "start": start_str,
            "end": end_str,
        }

    return templates.TemplateResponse("resident_invoices.html", {
        "request": request,
        "user": user,
        "items": items,
        "InvoiceStatus": InvoiceStatus,
        "status_val": status_val or "",
        "paid_map": paid_map,
        "period_map": period_map,
    })


# ---------------------- Деталь счёта (read-only) ----------------------

@router.get("/invoice/{invoice_id}", response_class=HTMLResponse)
def resident_invoice_detail(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    inv = db.get(Invoice, invoice_id)
    if not inv or (inv.resident not in (user.resident_links or [])):
        return RedirectResponse(url="/resident?error=forbidden", status_code=302)

    apps = (
        db.query(PaymentApplication)
          .join(Payment, Payment.id == PaymentApplication.payment_id)
          .filter(PaymentApplication.invoice_id == inv.id)
          .order_by(Payment.received_at.asc(), Payment.id.asc())
          .all()
    )
    paid_total = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                   .filter(PaymentApplication.invoice_id == inv.id).scalar() or 0
    left_total = (inv.amount_total or 0) - paid_total


    # --- НОВОЕ: период по показаниям (предыдущее → текущее) для ЭТОГО счета ---
    period_str = None
    # подзапрос: для каждого показания найдём предыдущее по тому же счётчику
    mr_with_prev = (
        db.query(
            MeterReading.id.label("mr_id"),
            MeterReading.resident_meter_id.label("meter_id"),
            MeterReading.reading_date.label("curr_dt"),
            func.lag(MeterReading.reading_date)
                .over(
                    partition_by=MeterReading.resident_meter_id,
                    order_by=MeterReading.reading_date
                )
                .label("prev_dt"),
        )
        .subquery("mr_with_prev")
    )

    row = (
        db.query(
            func.min(mr_with_prev.c.prev_dt).label("min_prev"),
            func.max(mr_with_prev.c.curr_dt).label("max_curr"),
        )
        .join(InvoiceLine, InvoiceLine.meter_reading_id == mr_with_prev.c.mr_id)
        .filter(InvoiceLine.invoice_id == inv.id)
        .one_or_none()
    )

    if row and row.max_curr:
        end_dt = row.max_curr
        start_dt = row.min_prev
        end_str = end_dt.date().strftime('%d.%m.%Y')
        start_str = start_dt.date().strftime('%d.%m.%Y') if start_dt else None

        if start_str and start_str != end_str:
            period_str = f"{start_str} - {end_str}"
        else:
            period_str = end_str


    return templates.TemplateResponse("resident_invoice_detail.html", {
        "request": request,
        "user": user,
        "inv": inv,
        "apps": apps,
        "paid_total": paid_total,
        "left_total": left_total,
        "period_str": period_str,
    })


# ---------------------- Сообщить об оплате ----------------------

@router.get("/report-payment", response_class=HTMLResponse)
def resident_report_payment_form(
    request: Request,
    db: Session = Depends(get_db),
    resident_id: str | None = None,
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    residents = user.resident_links or []
    preselect = None
    if resident_id and resident_id.strip().isdigit():
        rid = int(resident_id)
        if any(r.id == rid for r in residents):
            preselect = rid

    return templates.TemplateResponse("resident_report_payment.html", {
        "request": request,
        "user": user,
        "residents": residents,
        "PaymentMethod": PaymentMethod,
        "preselect": preselect,
    })


@router.post("/report-payment")
def resident_report_payment_submit(
    request: Request,
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
    received_at: str = Form(...),
    amount_total: Decimal = Form(...),
    method: str = Form("TRANSFER"),
    reference: str = Form(""),
    comment: str = Form(""),
):
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    rids = [r.id for r in (user.resident_links or [])]
    if resident_id not in rids:
        return RedirectResponse(url="/resident?error=forbidden", status_code=302)

    # Системное время Baku, чтобы фиксировать точный момент
    rcv = now_baku()

    if method not in {m.value for m in PaymentMethod}:
        method = PaymentMethod.TRANSFER.value

    p = Payment(
        resident_id=resident_id,
        received_at=rcv,
        amount_total=Decimal(amount_total),
        method=PaymentMethod(method),
        reference=(reference or None),
        comment=(comment or None),
        created_by_id=None,
    )
    db.add(p); db.commit()
    return RedirectResponse(url=f"/resident/invoices?ok=payment_reported&resident_id={resident_id}", status_code=302)


# ---------------------- Погасить из аванса ----------------------

@router.post("/apply-advance")
def resident_apply_advance(
    request: Request,
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
):
    """
    Ручной запуск авторазмещения аванса по открытым счетам резидента.
    """
    uid = get_user_id_from_session(request)
    if not uid:
        return RedirectResponse(url="/resident/login", status_code=302)
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return RedirectResponse(url="/resident/login", status_code=302)

    # проверим, что дом принадлежит пользователю
    if resident_id not in [r.id for r in (user.resident_links or [])]:
        return RedirectResponse(url="/resident?error=forbidden", status_code=302)

    try:
        affected = auto_apply_advance(db, resident_id)
        if affected:
            db.commit()
    except Exception:
        db.rollback()
        return RedirectResponse(url="/resident?error=advance_failed", status_code=302)

    return RedirectResponse(url="/resident?ok=advance_applied", status_code=302)
