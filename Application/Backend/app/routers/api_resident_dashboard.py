"""
API endpoint for resident dashboard data
Returns JSON data for the resident's personal dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models import (
    User, RoleEnum, Resident, ResidentMeter,
    Invoice, InvoiceStatus, InvoiceLine,
    Payment, PaymentApplication, PaymentMethod,
    Notification, NotificationStatus, MeterReading,
    user_residents, PaymentLog
)
from ..security import get_user_id_from_session
from ..utils import now_baku, to_baku_datetime


router = APIRouter(prefix="/api/resident", tags=["resident-api"])


@router.post("/apply-advance")
def api_resident_apply_advance(
    request: Request,
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
):
    """
    API версия применения аванса. 
    Берет аванс из общего пула и применяет к конкретному дому.
    """
    from .payments import auto_apply_advance
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Проверка прав (дом должен принадлежать пользователю)
    resident_ids = [r.id for r in (user.resident_links or [])]
    if resident_id not in resident_ids:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        # БЛОКИРОВКА: предотвращаем одновременные списания
        # Используем простой select без JOIN-ов для блокировки
        from sqlalchemy import select
        db.execute(select(Resident.id).where(Resident.id.in_(resident_ids)).with_for_update()).all()
        
        # 1) Применяем аванс к счетам (функция вернет количество и сумму)
        affected, applied_amount = auto_apply_advance(db, resident_id)
        
        if affected == 0 or applied_amount <= 0:
            return {
                "ok": True,
                "affected_count": 0,
                "message": "Нет открытых счетов для применения аванса"
            }
        
        # 2) Создаем техническую запись Payment для отображения в админ-панели
        history_payment = Payment(
            resident_id=resident_id,
            received_at=now_baku(),
            amount_total=applied_amount,
            method=PaymentMethod.ADVANCE,
            reference="AUTO_APPLY",
            comment=f"Автоматическое применение аванса к {affected} счетам ({applied_amount} ₼)",
            created_by_id=user.id,
        )
        db.add(history_payment)
        db.flush()
        
        # 3) ЛОГИРОВАНИЕ
        db.add(PaymentLog(
            payment_id=history_payment.id,
            resident_id=resident_id,
            user_id=user.id,
            action="APPLY_AUTO",
            amount=float(applied_amount),
            details=f"Автоматическое применение аванса к {affected} счетам"
        ))
            
        db.commit()
        return {
            "ok": True, 
            "affected_count": affected,
            "applied_amount": float(applied_amount),
            "message": f"Аванс успешно применен к {affected} счет(ам) на сумму {applied_amount} ₼"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
def test_endpoint():
    """Test endpoint to verify router is working."""
    return {"message": "API resident router is working!", "status": "ok"}


# Pydantic models for invoices
class InvoiceListItem(BaseModel):
    id: int
    resident_id: int
    resident_code: str  # "E / 444"
    number: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    period_year: int
    period_month: int
    amount_total: float
    paid_amount: float
    remaining_amount: float
    period_dates: Optional[dict] = None  # {"from": "05.12.2025", "to": "21.04.2026"}


class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceListItem]


@router.get("/invoices", response_model=InvoiceListResponse)
def get_resident_invoices(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    resident_id: Optional[int] = None,
):
    """
    Get list of invoices for the current resident user.
    Supports filtering by status and resident_id.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load user with residents relationship
    user_with_residents = (
        db.query(User)
        .options(joinedload(User.resident_links).joinedload(Resident.block))
        .filter(User.id == user.id)
        .first()
    )
    
    if not user_with_residents:
        raise HTTPException(status_code=401, detail="Unauthorized")

    resident_ids = [r.id for r in (user_with_residents.resident_links or [])]
    if not resident_ids:
        return {"invoices": []}

    # Filter by resident_id if specified and belongs to user
    if resident_id:
        if resident_id not in resident_ids:
            raise HTTPException(status_code=403, detail="Forbidden")
        resident_ids = [resident_id]

    # Query invoices
    query = db.query(Invoice).filter(Invoice.resident_id.in_(resident_ids))
    
    if status and status in {s.value for s in InvoiceStatus}:
        query = query.filter(Invoice.status == InvoiceStatus(status))
    
    items = query.order_by(
        Invoice.period_year.desc(),
        Invoice.period_month.desc(),
        Invoice.id.desc()
    ).all()

    # Get paid amounts
    paid_map = {}
    if items:
        ids = [inv.id for inv in items]
        rows = (
            db.query(
                PaymentApplication.invoice_id,
                func.coalesce(func.sum(PaymentApplication.amount_applied), 0)
            )
            .filter(PaymentApplication.invoice_id.in_(ids))
            .group_by(PaymentApplication.invoice_id)
            .all()
        )
        paid_map = {inv_id: float(paid) for inv_id, paid in rows}

    # Get period dates from meter readings (similar to resident_portal.py)
    period_map: dict[int, dict[str, Optional[str]]] = {}
    if items:
        ids = [inv.id for inv in items]
        from ..models import MeterReading
        
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
                "from": start_str,
                "to": end_str,
            }

    # Format response
    result = []
    for inv in items:
        resident = inv.resident
        block = resident.block if resident else None
        resident_code = f"{block.name if block else ''} / {resident.unit_number}" if block else resident.unit_number
        
        paid = paid_map.get(inv.id, 0.0)
        remaining = float(inv.amount_total or 0) - paid
        
        result.append({
            "id": inv.id,
            "resident_id": inv.resident_id,
            "resident_code": resident_code,
            "number": inv.number,
            "status": inv.status.value,
            "due_date": inv.due_date,
            "period_year": inv.period_year,
            "period_month": inv.period_month,
            "amount_total": float(inv.amount_total or 0),
            "paid_amount": paid,
            "remaining_amount": remaining,
            "period_dates": period_map.get(inv.id),
        })

    return {"invoices": result}


@router.get("/invoice/{invoice_id}")
def get_resident_invoice_detail(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific invoice for the current resident user.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load user with residents relationship
    user_with_residents = (
        db.query(User)
        .options(joinedload(User.resident_links))
        .filter(User.id == user.id)
        .first()
    )
    
    if not user_with_residents:
        raise HTTPException(status_code=401, detail="Unauthorized")

    resident_ids = [r.id for r in (user_with_residents.resident_links or [])]
    if not resident_ids:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Get invoice
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice belongs to user's residents
    if inv.resident_id not in resident_ids:
        raise HTTPException(status_code=403, detail="Forbidden")

    resident = inv.resident
    block = resident.block if resident else None
    
    # Get invoice lines
    lines = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all()
    
    # Get payments for this invoice
    apps = (
        db.query(PaymentApplication)
        .join(Payment, Payment.id == PaymentApplication.payment_id)
        .filter(PaymentApplication.invoice_id == inv.id)
        .order_by(PaymentApplication.created_at.asc(), PaymentApplication.id.asc())
        .all()
    )
    
    # Recalculate totals from lines
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
    
    paid_total = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                   .filter(PaymentApplication.invoice_id == inv.id).scalar() or 0
    remaining = float(inv.amount_total or 0) - float(paid_total)
    
    payments = []
    for app in apps:
        p = app.payment
        # ВАЖНО: Если app.reference == "ADVANCE", это списание из аванса
        # Показываем "ADVANCE" вместо реального метода платежа (CARD/TRANSFER)
        if app.reference == "ADVANCE":
            display_method = "ADVANCE"
            display_comment = "Royal Park Pass"
        else:
            display_method = p.method.value
            display_comment = p.comment or "—"

        payments.append({
            "id": app.id,
            "date": to_baku_datetime(app.created_at or p.created_at or p.received_at),
            "method": display_method,
            "amount": float(app.amount_applied),
            "payment_id": p.id,
            "reference": p.reference,
            "comment": display_comment,
        })
    
    # Format period dates from meter readings if available
    period_dates = None
    if lines:
        from ..models import MeterReading
        
        mr_with_prev = (
            db.query(
                MeterReading.id.label("mr_id"),
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
            .first()
        )
        
        if row and row.max_curr:
            end_str = row.max_curr.date().strftime('%d.%m.%Y')
            start_str = row.min_prev.date().strftime('%d.%m.%Y') if row.min_prev else None
            period_dates = {
                "from": start_str,
                "to": end_str,
            }
    
    resident_code = f"{block.name if block else ''} / {resident.unit_number}" if block else resident.unit_number
    
    return {
        "id": inv.id,
        "resident_id": inv.resident_id,
        "resident_code": resident_code,
        "number": inv.number,
        "status": inv.status.value,
        "due_date": inv.due_date,
        "notes": inv.notes,
        "period_year": inv.period_year,
        "period_month": inv.period_month,
        "period_dates": period_dates,
        "amount_net": float(inv.amount_net),
        "amount_vat": float(inv.amount_vat),
        "amount_total": float(inv.amount_total),
        "paid_amount": float(paid_total),
        "remaining_amount": remaining,
        "lines": [
            {
                "id": line.id,
                "description": line.description,
                "amount_net": float(line.amount_net),
                "amount_vat": float(line.amount_vat),
                "amount_total": float(line.amount_total),
            }
            for line in lines
        ],
        "payments": payments,
    }


@router.get("/detail/{resident_id}")
def get_resident_detail(
    resident_id: int,
    request: Request,
    db: Session = Depends(get_db),
    from_date: Optional[str] = None,  # YYYY-MM-DD
    to_date: Optional[str] = None,     # YYYY-MM-DD
    range_: Optional[str] = None,      # 'month' | '3m' | '6m' | 'year'
):
    """
    Get detailed information about a resident including meters and readings history.
    Supports date filtering.
    """
    try:
        user = _get_resident_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Load user with residents relationship
        user_with_residents = (
            db.query(User)
            .options(joinedload(User.resident_links).joinedload(Resident.block))
            .filter(User.id == user.id)
            .first()
        )
        
        if not user_with_residents:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Check if resident belongs to user and load with meters
        resident = (
            db.query(Resident)
            .options(joinedload(Resident.meters).joinedload(ResidentMeter.tariff))
            .options(joinedload(Resident.block))
            .filter(Resident.id == resident_id)
            .first()
        )
        if not resident or resident not in (user_with_residents.resident_links or []):
            raise HTTPException(status_code=403, detail="Forbidden")

        # Calculate date range
        start_dt: Optional[datetime] = None
        end_dt: Optional[datetime] = None
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
                    m += 12
                    y -= 1
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
                    m += 12
                    y -= 1
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
                    m += 12
                    y -= 1
                start_dt = datetime(y, m, 1)
                end_dt = datetime(
                    today.year + (1 if today.month == 12 else 0),
                    (1 if today.month == 12 else today.month + 1),
                    1
                )

        if start_dt is None and end_dt is None and (from_date or to_date):
            try:
                if from_date:
                    y, m, d = map(int, from_date.split("-"))
                    start_dt = datetime(y, m, d)
                if to_date:
                    y2, m2, d2 = map(int, to_date.split("-"))
                    end_dt = datetime(y2, m2, d2) + timedelta(days=1)
            except Exception:
                start_dt, end_dt = None, None

        # Get resident info
        block_name = resident.block.name if resident.block else ""
        resident_code = f"{block_name} / {resident.unit_number}" if block_name else resident.unit_number

        # Get meters with readings
        from ..models import MeterReading, MeterType
        
        meters_data = []
        # Ensure meters are loaded - they should already be loaded from the query above
        for meter in resident.meters if resident.meters else []:
            # Get readings for this meter with date filter
            readings_query = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == meter.id)
            )
            
            if start_dt is not None:
                readings_query = readings_query.filter(MeterReading.reading_date >= start_dt)
            if end_dt is not None:
                readings_query = readings_query.filter(MeterReading.reading_date < end_dt)
            
            readings = readings_query.order_by(
                MeterReading.reading_date.desc(),
                MeterReading.id.desc()
            ).all()

            # Determine meter type display name and unit
            if meter.meter_type == MeterType.ELECTRIC:
                display_type = "Электричество"
                unit = "кВт⋅ч"
            elif meter.meter_type == MeterType.GAS:
                display_type = "Газ"
                unit = "м³"
            elif meter.meter_type == MeterType.WATER:
                display_type = "Вода"
                unit = "м³"
            elif meter.meter_type == MeterType.SEWERAGE:
                display_type = "Канализация"
                unit = "м³"
            elif meter.meter_type == MeterType.SERVICE:
                display_type = "Сервис"
                unit = "мес."
            elif meter.meter_type == MeterType.RENT:
                display_type = "Аренда"
                unit = "мес."
            elif meter.meter_type == MeterType.CONSTRUCTION:
                display_type = "Строительство"
                unit = "мес."
            else:
                display_type = "Неизвестно"
                unit = "—"

            # Format readings
            readings_data = []
            for rd in readings:
                readings_data.append({
                    "id": rd.id,
                    "date": rd.reading_date.strftime("%d.%m.%Y"),
                    "reading": str(rd.value),
                    "consumption": str(rd.consumption),
                    "charge": float(rd.amount_total),
                    "vat": float(rd.vat_percent) if hasattr(rd, 'vat_percent') and rd.vat_percent else 0,
                    "comment": rd.note or "",
                })

            tariff_name = meter.tariff.name if meter.tariff else "—"
            
            meters_data.append({
                "id": meter.id,
                "type": meter.meter_type.value,
                "display_type": display_type,
                "serial_number": meter.serial_number,
                "tariff_name": tariff_name,
                "unit": unit,
                "readings": readings_data,
            })

        from_val = start_dt.strftime("%Y-%m-%d") if start_dt else ""
        to_val = (end_dt - timedelta(days=1)).strftime("%Y-%m-%d") if end_dt else ""

        return {
            "resident": {
                "id": resident.id,
                "code": resident_code,
                "block_name": block_name,
                "unit_number": resident.unit_number,
                "status": resident.status.value if resident.status else "unknown",
            },
            "meters": meters_data,
            "filters": {
                "from_date": from_val,
                "to_date": to_val,
                "range": range_ or "",
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in get_resident_detail: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ResidentDashboardData(BaseModel):
    id: int
    code: str  # "E / 444"
    month_due: float
    month_total: float
    month_paid: float
    debt_total: float
    advance_total: float
    pay_now: float
    due_date: Optional[date] = None
    due_state: str  # "ok" | "soon" | "over" | "none"


class DashboardSummary(BaseModel):
    total_month: float
    total_debt: float
    total_advance: float
    total_pay_now: float
    unpaid_invoices_count: int = 0
    monthly_kwh: float = 0.0
    monthly_water_m3: float = 0.0
    monthly_gas_m3: float = 0.0
    active_notifications_count: int = 0


class ResidentDashboardResponse(BaseModel):
    user: dict
    residents: List[ResidentDashboardData]
    summary: DashboardSummary


# --------- Appeals (resident requests) API, reusing Notification model ---------


class ResidentAppeal(BaseModel):
    id: int
    resident_id: int
    resident_code: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResidentAppealCreate(BaseModel):
    resident_id: int
    message: str


class ResidentAppealUpdate(BaseModel):
    message: str


def _get_resident_user(request: Request, db: Session) -> Optional[User]:
    """Get current resident user from session."""
    uid = get_user_id_from_session(request)
    if not uid:
        return None
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return None
    return user


@router.get("/appeals", response_model=List[ResidentAppeal])
def get_resident_appeals(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    List recent appeals (notifications) for current resident user.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    notifications = (
        db.query(Notification)
        .join(Resident, Resident.id == Notification.resident_id)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )

    result: List[ResidentAppeal] = []
    for notif in notifications:
        block_name = notif.resident.block.name if notif.resident and notif.resident.block else ""
        unit_number = notif.resident.unit_number if notif.resident else ""
        resident_code = f"{block_name} / {unit_number}" if block_name and unit_number else unit_number or block_name or ""
        result.append(
            ResidentAppeal(
                id=notif.id,
                resident_id=notif.resident_id or 0,
                resident_code=resident_code,
                message=notif.message,
                status=notif.status.value,
                created_at=notif.created_at,
            )
        )

    return result


@router.post("/appeals", response_model=ResidentAppeal)
def create_resident_appeal(
    data: ResidentAppealCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Create new appeal from current resident user.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    message = (data.message or "").strip()
    if len(message) < 5:
        raise HTTPException(status_code=400, detail="Message is too short")

    resident = db.get(Resident, data.resident_id)
    if not resident or resident not in (user.resident_links or []):
        raise HTTPException(status_code=403, detail="Invalid resident")

    notif = Notification(
        user_id=user.id,
        resident_id=resident.id,
        message=message,
        status=NotificationStatus.UNREAD,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    block_name = resident.block.name if resident.block else ""
    resident_code = f"{block_name} / {resident.unit_number}" if block_name else resident.unit_number

    return ResidentAppeal(
        id=notif.id,
        resident_id=notif.resident_id or 0,
        resident_code=resident_code,
        message=notif.message,
        status=notif.status.value,
        created_at=notif.created_at,
    )


@router.put("/appeals/{appeal_id}", response_model=ResidentAppeal)
def update_resident_appeal(
    appeal_id: int,
    data: ResidentAppealUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update appeal text for current resident user (only while UNREAD).
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    notif = db.get(Notification, appeal_id)
    if not notif or notif.user_id != user.id:
        raise HTTPException(status_code=404, detail="Appeal not found")

    if notif.status != NotificationStatus.UNREAD:
        raise HTTPException(status_code=400, detail="Cannot edit read appeal")

    message = (data.message or "").strip()
    if len(message) < 5:
        raise HTTPException(status_code=400, detail="Message is too short")

    notif.message = message
    db.commit()
    db.refresh(notif)

    resident = notif.resident
    block_name = resident.block.name if resident and resident.block else ""
    unit_number = resident.unit_number if resident else ""
    resident_code = f"{block_name} / {unit_number}" if block_name and unit_number else unit_number or block_name or ""

    return ResidentAppeal(
        id=notif.id,
        resident_id=notif.resident_id or 0,
        resident_code=resident_code,
        message=notif.message,
        status=notif.status.value,
        created_at=notif.created_at,
    )


@router.delete("/appeals/{appeal_id}")
def delete_resident_appeal(
    appeal_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Delete appeal for current resident user.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    notif = db.get(Notification, appeal_id)
    if not notif or notif.user_id != user.id:
        raise HTTPException(status_code=404, detail="Appeal not found")

    db.delete(notif)
    db.commit()

    return {"ok": True}


# --------- Resident Payment API ---------


class ResidentPaymentCreate(BaseModel):
    resident_id: int
    amount: float
    method: str = "CARD"  # CARD, TRANSFER, CASH, ONLINE
    reference: Optional[str] = None
    comment: Optional[str] = None
    scope: Optional[str] = None  # 'month' - только текущий месяц, 'all' - все счета, None - только пополнение аванса


class ResidentPaymentResponse(BaseModel):
    ok: bool
    payment_id: int
    message: str


@router.post("/payment", response_model=ResidentPaymentResponse)
def create_resident_payment(
    data: ResidentPaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Create a payment from the resident portal.
    This endpoint allows authenticated resident users to submit payments.
    The payment will be automatically applied to open invoices based on scope:
    - scope='month': only current month invoices
    - scope='all': all open invoices
    - scope=None: no application (advance top-up only)
    """
    from ..models import Payment, PaymentMethod
    
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load user with residents relationship
    user_with_residents = (
        db.query(User)
        .options(joinedload(User.resident_links))
        .filter(User.id == user.id)
        .first()
    )
    
    if not user_with_residents:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate resident belongs to user
    resident_ids = [r.id for r in (user_with_residents.resident_links or [])]
    if data.resident_id not in resident_ids:
        raise HTTPException(status_code=403, detail="Invalid resident")

    # Validate amount
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Validate payment method
    method_value = data.method.upper()
    is_advance = (method_value == "ADVANCE")
    
    if not is_advance:
        valid_methods = {m.value for m in PaymentMethod}
        if method_value not in valid_methods:
            # Если это не аванс и не известный метод, то для онлайн-оплат из портала 
            # мы разрешаем только CARD или TRANSFER. 
            # Если пришло что-то странное - принудительно ставим CARD.
            method_value = "CARD"

    from .payments import apply_payment_to_invoices, apply_advance_with_limit
    
    # Если оплата через аванс, создаем историю списания и корректируем общий баланс
    if is_advance:
        # БЛОКИРОВКА: предотвращаем одновременные списания аванса
        # Используем простой select без JOIN-ов для блокировки
        from sqlalchemy import select
        db.execute(select(Resident.id).where(Resident.id.in_(resident_ids)).with_for_update()).all()
        
        # 1) Проверяем наличие средств в авансе перед списанием
        total_advance = Decimal("0")
        if resident_ids:
            from sqlalchemy import cast, String
            all_user_payments = db.query(Payment).filter(
                Payment.resident_id.in_(resident_ids),
                cast(Payment.method, String) != 'ADVANCE'
            ).all()
            for p in all_user_payments:
                applied_p = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                              .filter(PaymentApplication.payment_id == p.id).scalar() or 0
                total_advance += (Decimal(p.amount_total or 0) - Decimal(applied_p))
        
        target_amount = Decimal(str(data.amount))
        if total_advance < target_amount:
            raise HTTPException(status_code=400, detail=f"Недостаточно средств на авансе (доступно {total_advance} ₼)")

        try:
            # 2) Списываем реальные деньги из существующих платежей
            # Это создаст PaymentApplication с reference="ADVANCE" к реальным платежам
            # Если scope не указан, по умолчанию бьем только текущий месяц,
            # чтобы не разбрасывать оплату по старым долгам.
            effective_scope = data.scope if data.scope in ("all", "month") else "month"

            affected_count = apply_advance_with_limit(
                db,
                user.id,
                data.resident_id,
                max_amount=target_amount,
                scope=effective_scope
            )
            
            # 3) Создаем технический Payment (метод ADVANCE) ТОЛЬКО для истории
            # ВАЖНО: Мы НЕ создаем PaymentApplication для этого платежа, 
            # так как приложения уже созданы от реальных платежей в apply_advance_with_limit.
            history_payment = Payment(
                resident_id=data.resident_id,
                received_at=now_baku(),
                amount_total=target_amount,
                method=PaymentMethod.ADVANCE,
                reference="ADVANCE_USE",
                comment=f"Списание из аванса: {target_amount} ₼" + (f" (к {affected_count} счетам)" if affected_count > 0 else ""),
                created_by_id=user.id,
            )
            db.add(history_payment)
            db.flush()
            
            # ЛОГИРОВАНИЕ действия
            db.add(PaymentLog(
                payment_id=history_payment.id,
                resident_id=data.resident_id,
                user_id=user.id,
                action="ADVANCE_USE",
                amount=float(target_amount),
                details=f"Списание из аванса. Распределено по {affected_count} счетам."
            ))
            
            db.commit()
            
            if data.scope is None:
                message = "Аванс зарезервирован (scope=None)"
            elif affected_count > 0:
                message = f"Аванс успешно применён к {affected_count} счёт(ам)"
            else:
                message = f"Аванс не применён (нет подходящих открытых счетов)"
                
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке аванса: {str(e)}")
        
        return ResidentPaymentResponse(
            ok=True,
            payment_id=history_payment.id,
            message=message
        )
    
    # Для обычных платежей (CARD, TRANSFER и т.д.) создаем новый платеж
    payment = Payment(
        resident_id=data.resident_id,
        received_at=now_baku(),
        amount_total=Decimal(str(data.amount)),
        method=PaymentMethod(method_value),
        reference=data.reference or None,
        comment=data.comment or f"Онлайн-оплата через личный кабинет",
        created_by_id=None,  # Self-payment by resident
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # ЛОГИРОВАНИЕ создания
    db.add(PaymentLog(
        payment_id=payment.id,
        resident_id=data.resident_id,
        user_id=user.id,
        action="CREATE",
        amount=float(data.amount),
        details=f"Онлайн-оплата (метод: {method_value})"
    ))

    # Apply payment to invoices based on scope
    # scope='month' - только текущий месяц, 'all' - все счета, None - только пополнение аванса
    try:
        affected_count = apply_payment_to_invoices(
            db, 
            payment.id, 
            data.resident_id, 
            scope=data.scope
        )
        db.commit()
        
        if data.scope is None:
            message = "Платёж успешно создан (пополнение аванса)"
        elif affected_count > 0:
            message = f"Платёж успешно создан и применён к {affected_count} счёт(ам)"
        else:
            message = "Платёж успешно создан (не применён к счетам - нет подходящих счетов)"
    except Exception as e:
        print(f"Warning: apply_payment_to_invoices failed: {e}")
        # Payment still created, just not applied
        message = "Платёж успешно создан, но не применён к счетам"

    return ResidentPaymentResponse(
        ok=True,
        payment_id=payment.id,
        message=message
    )


@router.get("/dashboard", response_model=ResidentDashboardResponse)
def get_resident_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get dashboard data for the current resident user.
    Returns financial summary: month due, debt, advance, pay now.
    """
    user = _get_resident_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load user with residents relationship
    user_with_residents = (
        db.query(User)
        .options(joinedload(User.resident_links).joinedload(Resident.block))
        .filter(User.id == user.id)
        .first()
    )
    
    if not user_with_residents:
        raise HTTPException(status_code=401, detail="Unauthorized")

    residents = user_with_residents.resident_links or []
    today = datetime.utcnow().date()
    cur_y, cur_m = today.year, today.month

    # Calculate financial data for each resident
    month_due: dict[int, Decimal] = {}
    month_total: dict[int, Decimal] = {}
    month_paid: dict[int, Decimal] = {}
    total_debt_per_res: dict[int, Decimal] = {}
    due_info: dict[int, dict] = {}

    resident_ids = [r.id for r in residents]

    # Global advance calculation for the user
    # Calculate leftover for each payment belonging to the user's residents
    total_advance_calc = Decimal("0")
    if resident_ids:
        # Get all payments (excluding ADVANCE records)
        from sqlalchemy import cast, String
        all_user_payments = db.query(Payment).filter(
            Payment.resident_id.in_(resident_ids),
            cast(Payment.method, String) != 'ADVANCE'
        ).all()
        for p in all_user_payments:
            # Sum of applications for THIS payment
            applied_p = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                          .filter(PaymentApplication.payment_id == p.id).scalar() or 0
            left = Decimal(p.amount_total or 0) - Decimal(applied_p)
            total_advance_calc += left
    
    shared_advance = total_advance_calc
    if shared_advance < 0: shared_advance = Decimal("0")

    for r in residents:
        # Current month invoice
        inv_month = (
            db.query(Invoice)
            .filter(
                Invoice.resident_id == r.id,
                Invoice.period_year == cur_y,
                Invoice.period_month == cur_m,
                Invoice.status != InvoiceStatus.CANCELED
            )
            .first()
        )
        
        if inv_month:
            paid_m = (
                db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
                .filter(PaymentApplication.invoice_id == inv_month.id)
                .scalar() or 0
            )
            md = Decimal(inv_month.amount_total or 0) - Decimal(paid_m)
            month_due[r.id] = md if md > 0 else Decimal("0")
            month_total[r.id] = Decimal(inv_month.amount_total or 0)
            month_paid[r.id] = Decimal(paid_m)

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
            month_due[r.id] = Decimal("0")
            month_total[r.id] = Decimal("0")
            month_paid[r.id] = Decimal("0")
            due_info[r.id] = {"due_date": None, "state": "none"}

        # Total debt across all invoices
        inv_total = (
            db.query(func.coalesce(func.sum(Invoice.amount_total), 0))
            .filter(
                Invoice.resident_id == r.id,
                Invoice.status != InvoiceStatus.CANCELED
            )
            .scalar() or 0
        )
        paid_total = (
            db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
            .join(Invoice, Invoice.id == PaymentApplication.invoice_id)
            .filter(
                Invoice.resident_id == r.id,
                Invoice.status != InvoiceStatus.CANCELED
            )
            .scalar() or 0
        )
        debt = Decimal(inv_total) - Decimal(paid_total)
        total_debt_per_res[r.id] = debt if debt > 0 else Decimal("0")

    # Summary across all residents
    total_month_due = sum(month_due.values(), Decimal("0"))
    total_debt = sum(total_debt_per_res.values(), Decimal("0"))
    
    # Pay now = total debt - shared advance (minimum 0)
    # This reflects the potential to pay EVERYTHING from the shared pool
    total_pay_now = max(total_debt - shared_advance, Decimal("0"))

    # Count unpaid invoices
    unpaid_count = 0
    if resident_ids:
        unpaid_count = (
            db.query(func.count(Invoice.id))
            .filter(
                Invoice.resident_id.in_(resident_ids),
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.DRAFT])
            )
            .scalar() or 0
        )
        # Also count invoices with remaining amount
        unpaid_with_remaining = db.query(Invoice).filter(
            Invoice.resident_id.in_(resident_ids),
            Invoice.status != InvoiceStatus.CANCELED
        ).all()
        for inv in unpaid_with_remaining:
            paid = (
                db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
                .filter(PaymentApplication.invoice_id == inv.id)
                .scalar() or 0
            )
            if float(inv.amount_total or 0) - float(paid) > 0.01:
                if inv.status not in [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.DRAFT]:
                    unpaid_count += 1

    # Calculate monthly utility consumptions (electricity, water, gas)
    monthly_kwh = Decimal("0")
    monthly_water_m3 = Decimal("0")
    monthly_gas_m3 = Decimal("0")
    if resident_ids:
        today_now = datetime.utcnow()
        month_start = datetime(today_now.year, today_now.month, 1)
        month_end = datetime(today_now.year + (1 if today_now.month == 12 else 0), 
                             (1 if today_now.month == 12 else today_now.month + 1), 1)
        
        from ..models import MeterType
        
        # Electricity consumption
        electric_readings = (
            db.query(MeterReading)
            .join(ResidentMeter, ResidentMeter.id == MeterReading.resident_meter_id)
            .filter(
                ResidentMeter.resident_id.in_(resident_ids),
                ResidentMeter.meter_type == MeterType.ELECTRIC,
                MeterReading.reading_date >= month_start,
                MeterReading.reading_date < month_end
            )
            .all()
        )
        monthly_kwh = sum(Decimal(str(rd.consumption or 0)) for rd in electric_readings)
        
        # Water consumption
        water_readings = (
            db.query(MeterReading)
            .join(ResidentMeter, ResidentMeter.id == MeterReading.resident_meter_id)
            .filter(
                ResidentMeter.resident_id.in_(resident_ids),
                ResidentMeter.meter_type == MeterType.WATER,
                MeterReading.reading_date >= month_start,
                MeterReading.reading_date < month_end
            )
            .all()
        )
        monthly_water_m3 = sum(Decimal(str(rd.consumption or 0)) for rd in water_readings)
        
        # Gas consumption
        gas_readings = (
            db.query(MeterReading)
            .join(ResidentMeter, ResidentMeter.id == MeterReading.resident_meter_id)
            .filter(
                ResidentMeter.resident_id.in_(resident_ids),
                ResidentMeter.meter_type == MeterType.GAS,
                MeterReading.reading_date >= month_start,
                MeterReading.reading_date < month_end
            )
            .all()
        )
        monthly_gas_m3 = sum(Decimal(str(rd.consumption or 0)) for rd in gas_readings)

    # Count active notifications
    active_notifications = 0
    if user:
        active_notifications = (
            db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user.id,
                Notification.status == NotificationStatus.UNREAD
            )
            .scalar() or 0
        )

    # Format resident data
    residents_data = []
    
    for r in residents:
        block_name = r.block.name if r.block else ""
        code = f"{block_name} / {r.unit_number}" if block_name else r.unit_number
        
        # Общий долг по этому дому (все счета)
        total_res_debt = total_debt_per_res.get(r.id, Decimal("0"))
        
        # Долг за предыдущие периоды (все минус текущий месяц)
        # Если в карточке мы отдельно показываем "К оплате за месяц", то "Долг" должен быть остатком
        res_month_due = month_due.get(r.id, Decimal("0"))
        res_overdue_debt = max(total_res_debt - res_month_due, Decimal("0"))
        
        # К ОПЛАТЕ СЕЙЧАС для конкретного дома:
        # Теперь это просто долг этого дома (включая текущий месяц), 
        # БЕЗ учета общего аванса, так как списание не происходит автоматически.
        res_pay_now = total_res_debt
        
        residents_data.append(ResidentDashboardData(
            id=r.id,
            code=code,
            month_due=float(res_month_due),
            month_total=float(month_total.get(r.id, Decimal("0"))),
            month_paid=float(month_paid.get(r.id, Decimal("0"))),
            debt_total=float(res_overdue_debt), # Теперь показываем только просроченный долг
            advance_total=float(shared_advance), # Показываем ОБЩИЙ аванс на всех карточках
            pay_now=float(res_pay_now),
            due_date=due_info.get(r.id, {}).get("due_date"),
            due_state=due_info.get(r.id, {}).get("state", "none"),
        ))

    return ResidentDashboardResponse(
        user={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "email": user.email,
        },
        residents=residents_data,
        summary=DashboardSummary(
            total_month=float(total_month_due),
            total_debt=float(total_debt),
            total_advance=float(shared_advance),
            total_pay_now=float(total_pay_now),
            unpaid_invoices_count=unpaid_count,
            monthly_kwh=float(monthly_kwh),
            monthly_water_m3=float(monthly_water_m3),
            monthly_gas_m3=float(monthly_gas_m3),
            active_notifications_count=active_notifications,
        ),
    )

