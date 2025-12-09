"""
API endpoint for resident dashboard data
Returns JSON data for the resident's personal dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Request
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
)
from ..security import get_user_id_from_session


router = APIRouter(prefix="/api/resident", tags=["resident-api"])


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
        .order_by(Payment.received_at.asc(), Payment.id.asc())
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
        payments.append({
            "id": app.id,
            "date": p.received_at.date() if p.received_at else None,
            "method": p.method.value,
            "amount": float(app.amount_applied),
            "payment_id": p.id,
            "reference": p.reference,
            "comment": p.comment,
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
    active_notifications_count: int = 0


class ResidentDashboardResponse(BaseModel):
    user: dict
    residents: List[ResidentDashboardData]
    summary: DashboardSummary


def _get_resident_user(request: Request, db: Session) -> Optional[User]:
    """Get current resident user from session."""
    uid = get_user_id_from_session(request)
    if not uid:
        return None
    user = db.get(User, uid)
    if not user or user.role != RoleEnum.RESIDENT or not user.is_active:
        return None
    return user


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
    debt_total: dict[int, Decimal] = {}
    advance_total: dict[int, Decimal] = {}
    pay_now: dict[int, Decimal] = {}
    due_info: dict[int, dict] = {}

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
        debt_total[r.id] = debt if debt > 0 else Decimal("0")

        # Advance (free balance from payments)
        # Sum of all payments for this resident
        pay_sum = (
            db.query(func.coalesce(func.sum(Payment.amount_total), 0))
            .filter(Payment.resident_id == r.id)
            .scalar() or 0
        )
        # Sum of all payment applications (how much was applied to invoices)
        appl_sum = (
            db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
            .join(Payment, Payment.id == PaymentApplication.payment_id)
            .filter(Payment.resident_id == r.id)
            .scalar() or 0
        )
        # Advance = total payments - applied payments (free balance)
        adv = Decimal(pay_sum) - Decimal(appl_sum)
        advance_total[r.id] = adv if adv > 0 else Decimal("0")

        # Pay now = debt - advance (minimum 0)
        pay_now[r.id] = max(debt_total[r.id] - advance_total[r.id], Decimal("0"))

    # Summary across all residents
    total_month = sum(month_due.values(), Decimal("0"))
    total_debt = sum(debt_total.values(), Decimal("0"))
    total_adv = sum(advance_total.values(), Decimal("0"))
    total_pay = sum(pay_now.values(), Decimal("0"))

    # Count unpaid invoices
    resident_ids = [r.id for r in residents]
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

    # Calculate monthly kWh consumption
    monthly_kwh = Decimal("0")
    if resident_ids:
        today = datetime.utcnow()
        month_start = datetime(today.year, today.month, 1)
        month_end = datetime(today.year + (1 if today.month == 12 else 0), 
                             (1 if today.month == 12 else today.month + 1), 1)
        
        from ..models import MeterType
        readings = (
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
        monthly_kwh = sum(Decimal(str(rd.consumption or 0)) for rd in readings)

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
        
        residents_data.append(ResidentDashboardData(
            id=r.id,
            code=code,
            month_due=float(month_due.get(r.id, Decimal("0"))),
            month_total=float(month_total.get(r.id, Decimal("0"))),
            month_paid=float(month_paid.get(r.id, Decimal("0"))),
            debt_total=float(debt_total.get(r.id, Decimal("0"))),
            advance_total=float(advance_total.get(r.id, Decimal("0"))),
            pay_now=float(pay_now.get(r.id, Decimal("0"))),
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
            total_month=float(total_month),
            total_debt=float(total_debt),
            total_advance=float(total_adv),
            total_pay_now=float(total_pay),
            unpaid_invoices_count=unpaid_count,
            monthly_kwh=float(monthly_kwh),
            active_notifications_count=active_notifications,
        ),
    )

