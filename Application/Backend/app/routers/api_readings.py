from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, exists

from ..database import get_db
from ..models import (
    User, RoleEnum, Block, Resident, ResidentMeter,
    MeterType, Tariff, MeterReading, ReadingLog,
    Invoice, InvoiceLine, InvoiceStatus
)
from ..deps import get_current_user
from .readings import compute_amount
from .payments import auto_apply_advance


router = APIRouter(prefix="/api/readings", tags=["readings-api"])


# Pydantic models
class MeterReadingOut(BaseModel):
    id: int
    resident_meter_id: int
    reading_date: datetime
    value: float
    consumption: float
    tariff_id: int
    tariff_name: Optional[str] = None
    amount_net: float
    vat_percent: int
    amount_vat: float
    amount_total: float
    note: Optional[str] = None

    class Config:
        from_attributes = True


class ResidentReadingRow(BaseModel):
    resident_id: int
    resident_code: str  # "A / 41"
    resident_info: str  # "Блок A, №41"
    block_name: str
    unit_number: str
    meters: List[dict]  # [{type, consumption, unit, total}]
    total_amount: float
    is_paid: bool


class ReadingCreateItem(BaseModel):
    meter_id: int
    new_value: Optional[float] = None  # None для фикс-услуг означает удаление


class ReadingCreate(BaseModel):
    resident_id: int
    date_str: str  # "YYYY-MM-DD"
    items: List[ReadingCreateItem]
    note: Optional[str] = None


# ====== List readings ======
@router.get("/")
def list_readings(
    db: Session = Depends(get_db),
    block_id: Optional[int] = Query(None),
    resident_id: Optional[int] = Query(None),
    meter_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    """
    Список показаний за выбранный месяц (агрегировано по резидентам).
    """
    blocks = db.query(Block).order_by(Block.name.asc()).all()

    # Выпадашка резидентов (по блоку/поиску)
    residents_q = db.query(Resident).order_by(Resident.unit_number.asc())
    if block_id:
        residents_q = residents_q.filter(Resident.block_id == block_id)
    if q:
        like = f"%{q.strip()}%"
        residents_q = residents_q.filter(
            (Resident.unit_number.ilike(like)) |
            (Resident.owner_full_name.ilike(like)) |
            (Resident.owner_phone.ilike(like)) |
            (Resident.owner_email.ilike(like))
        )
    residents = residents_q.all()

    now = datetime.utcnow()
    year = year or now.year
    month = month or now.month

    from_dt = datetime(year, month, 1)
    to_dt = datetime(year + (1 if month == 12 else 0), (1 if month == 12 else month + 1), 1)

    # Показания за период
    # ВАЖНО: Показываем показания для всех счётчиков (активных и неактивных),
    # так как показания уже были записаны и должны отображаться в истории
    readings_q = db.query(MeterReading).join(ResidentMeter).join(Resident)
    # УБРАЛИ фильтр is_active == True, чтобы показывать все показания за период
    if block_id:
        readings_q = readings_q.filter(Resident.block_id == block_id)
    if resident_id:
        readings_q = readings_q.filter(Resident.id == resident_id)
    if meter_type in {"ELECTRIC", "GAS", "WATER", "SEWERAGE", "SERVICE", "RENT", "CONSTRUCTION"}:
        readings_q = readings_q.filter(ResidentMeter.meter_type == MeterType(meter_type))
    if q:
        like = f"%{q.strip()}%"
        readings_q = readings_q.filter(
            (Resident.unit_number.ilike(like)) |
            (Resident.owner_full_name.ilike(like)) |
            (Resident.owner_phone.ilike(like)) |
            (Resident.owner_email.ilike(like))
        )

    readings_q = readings_q.filter(
        MeterReading.reading_date >= from_dt,
        MeterReading.reading_date < to_dt,
    )
    period_readings = readings_q.all()
    
    # Агрегат по счётчикам
    rows: dict[int, dict] = {}
    for rd in period_readings:
        meter = rd.resident_meter
        res_id = meter.resident_id

        # Единицы: ELECTRIC -> кВт·ч; GAS/WATER/SEWERAGE -> м³; SERVICE/RENT/CONSTRUCTION -> мес.
        if meter.meter_type == MeterType.ELECTRIC:
            unit = "кВт·ч"
        elif meter.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE}:
            unit = "м³"
        else:
            unit = "мес."

        entry = rows.setdefault(res_id, {"resident": meter.resident, "meters": {}})
        mrow = entry["meters"].setdefault(meter.id, {
            "meter": meter,
            "unit": unit,
            "consumption": Decimal("0"),
            "total": Decimal("0"),
        })
        mrow["consumption"] += Decimal(rd.consumption)
        mrow["total"] += Decimal(rd.amount_total)

    paid_resident_ids = set(
        rid for (rid,) in db.query(Resident.id)
        .join(Invoice, Invoice.resident_id == Resident.id)
        .filter(
            Invoice.period_year == year,
            Invoice.period_month == month,
            Invoice.status == InvoiceStatus.PAID
        ).all()
    )

    # Формируем ответ
    result_rows = []
    for res_id, data in rows.items():
        resident = data["resident"]
        meters_list = []
        total_amount = Decimal("0")
        reading_date = None  # Get first reading date for this resident
        
        for meter_id, mdata in data["meters"].items():
            meter = mdata["meter"]
            consumption = float(mdata["consumption"])
            total = float(mdata["total"])
            total_amount += Decimal(total)
            
            # Get reading date from first reading for this meter
            if not reading_date:
                first_reading = (
                    db.query(MeterReading)
                    .filter(
                        MeterReading.resident_meter_id == meter.id,
                        MeterReading.reading_date >= from_dt,
                        MeterReading.reading_date < to_dt,
                    )
                    .order_by(MeterReading.reading_date.asc(), MeterReading.id.asc())
                    .first()
                )
                if first_reading:
                    reading_date = first_reading.reading_date
            
            # Определяем тип для отображения
            if meter.meter_type == MeterType.ELECTRIC:
                display_type = "Электричество"
            elif meter.meter_type == MeterType.GAS:
                display_type = "Газ"
            elif meter.meter_type == MeterType.WATER:
                display_type = "Вода"
            elif meter.meter_type == MeterType.SEWERAGE:
                display_type = "Канализация"
            elif meter.meter_type == MeterType.SERVICE:
                display_type = "Сервис"
            elif meter.meter_type == MeterType.RENT:
                display_type = "Аренда"
            elif meter.meter_type == MeterType.CONSTRUCTION:
                display_type = "Строительство"
            else:
                display_type = "Неизвестно"
            
            meters_list.append({
                "type": display_type,
                "consumption": consumption,
                "unit": mdata["unit"],
                "total": total,
            })
        
        result_rows.append({
            "resident_id": res_id,
            "resident_code": f"{resident.block.name if resident.block else ''} / {resident.unit_number}",
            "resident_info": f"Блок {resident.block.name if resident.block else ''}, №{resident.unit_number}",
            "block_name": resident.block.name if resident.block else "",
            "unit_number": resident.unit_number,
            "meters": meters_list,
            "total_amount": float(total_amount),
            "is_paid": res_id in paid_resident_ids,
            "reading_date": reading_date.strftime("%Y-%m-%d") if reading_date else None,
        })

    # Apply pagination
    total = len(result_rows)
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_rows = result_rows[start_idx:end_idx]

    return {
        "blocks": [{"id": b.id, "name": b.name} for b in blocks],
        "residents": [{"id": r.id, "unit_number": r.unit_number, "block_name": r.block.name if r.block else ""} for r in residents],
        "rows": paginated_rows,
        "year": year,
        "month": month,
        "total_amount": float(sum(r["total_amount"] for r in result_rows)),
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
        },
    }


# ====== Get resident meters (reuse existing endpoint) ======
@router.get("/resident/{resident_id}/meters")
def get_resident_meters(
    resident_id: int,
    db: Session = Depends(get_db),
    date: Optional[str] = Query(default=None, description="YYYY-MM-DD для режима редактирования"),
):
    """
    Данные для модалки: список счётчиков резидента.
    """
    r = db.get(Resident, resident_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")

    period_start = period_end = None
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            period_start = datetime(d.year, d.month, 1)
            period_end = datetime(d.year + (1 if d.month == 12 else 0), (1 if d.month == 12 else d.month + 1), 1)
        except Exception as e:
            period_start = period_end = None

    # ВАЖНО: В режиме редактирования месяца нужно показывать:
    # - активные счётчики
    # - И неактивные тоже, если в выбранном месяце по ним есть показания
    # иначе при “удалении услуги у резидента” (deactivate meter) пропадёт возможность
    # открыть/увидеть исторический тариф и редактировать показания.
    meters_q = db.query(ResidentMeter).filter(ResidentMeter.resident_id == resident_id)
    if period_start and period_end:
        in_period = exists().where(
            MeterReading.resident_meter_id == ResidentMeter.id,
            MeterReading.reading_date >= period_start,
            MeterReading.reading_date < period_end,
        )
        meters_q = meters_q.filter(or_(ResidentMeter.is_active == True, in_period))  # noqa: E712
    else:
        meters_q = meters_q.filter(ResidentMeter.is_active == True)  # noqa: E712

    meters_list = meters_q.options(
        joinedload(ResidentMeter.tariff).joinedload(Tariff.steps)
    ).all()
    
    meters = []
    for m in meters_list:
        # prev_value: ПОСЛЕДНЯЯ запись ДО начала месяца (или initial)
        if period_start:
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            if prev_rd:
                prev_value = Decimal(prev_rd.value)
            else:
                prev_value = Decimal(m.initial_reading or 0)
        else:
            # без даты — просто последнее показание
            last_any = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            if last_any:
                prev_value = Decimal(last_any.value)
            else:
                prev_value = Decimal(m.initial_reading or 0)

        existing = None
        if period_start and period_end:
            existing = (
                db.query(MeterReading)
                .filter(
                    MeterReading.resident_meter_id == m.id,
                    MeterReading.reading_date >= period_start,
                    MeterReading.reading_date < period_end,
                )
                .options(joinedload(MeterReading.tariff).joinedload(Tariff.steps))
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )

        # ВАЖНО:
        # Для режима редактирования месяца (когда existing=True) нужно показывать тариф,
        # по которому было рассчитано ИМЕННО ЭТО показание (existing.tariff),
        # а не текущий тариф счётчика (m.tariff), т.к. тариф могли "удалить" (архивировать)
        # или поменять у счётчика позже.
        tariff_obj = None
        if existing and getattr(existing, "tariff", None) is not None:
            tariff_obj = existing.tariff
        else:
            tariff_obj = m.tariff

        if m.meter_type == MeterType.ELECTRIC:
            display_type = "Электричество"; unit = "кВт·ч"; is_fixed = False
        elif m.meter_type == MeterType.GAS:
            display_type = "Газ"; unit = "м³"; is_fixed = False
        elif m.meter_type == MeterType.WATER:
            display_type = "Вода"; unit = "м³"; is_fixed = False
        elif m.meter_type == MeterType.SEWERAGE:
            display_type = "Канализация"; unit = "м³"; is_fixed = False
        elif m.meter_type == MeterType.SERVICE:
            display_type = "Сервис (фикс)"; unit = "мес."; is_fixed = True
        elif m.meter_type == MeterType.RENT:
            display_type = "Аренда (фикс)"; unit = "мес."; is_fixed = True
        elif m.meter_type == MeterType.CONSTRUCTION:
            display_type = "Строительство (фикс)"; unit = "мес."; is_fixed = True
        else:
            display_type = "Неизвестно"; unit = "—"; is_fixed = False

        # Для CONSTRUCTION тарифов получаем диапазон дат
        date_range = None
        if m.meter_type == MeterType.CONSTRUCTION and tariff_obj and tariff_obj.steps:
            first_step = tariff_obj.steps[0]
            if first_step.from_date and first_step.to_date:
                date_range = {
                    "from_date": first_step.from_date.isoformat(),
                    "to_date": first_step.to_date.isoformat(),
                }

        # Подготовка данных о тарифе для расчета суммы на frontend
        tariff_steps = []
        if tariff_obj and tariff_obj.steps:
            for step in sorted(tariff_obj.steps, key=lambda s: s.from_value or 0):
                tariff_steps.append({
                    "from_value": float(step.from_value) if step.from_value is not None else None,
                    "to_value": float(step.to_value) if step.to_value is not None else None,
                    "from_date": step.from_date.isoformat() if step.from_date else None,
                    "to_date": step.to_date.isoformat() if step.to_date else None,
                    "price": float(step.price),
                })
        
        prev_value_float = float(prev_value)
        existing_value_float = float(existing.value) if existing else None
        
        meters.append({
            "meter_id": m.id,
            "type": m.meter_type.value,
            "display_type": display_type,
            "serial": m.serial_number,
            "tariff_id": (existing.tariff_id if existing else m.tariff_id),
            "tariff_name": (tariff_obj.name if tariff_obj else None),
            "vat_percent": (tariff_obj.vat_percent if tariff_obj else 0),
            "tariff_steps": tariff_steps,
            "prev_value": prev_value_float,
            "unit": unit,
            "is_fixed": is_fixed,
            "date_range": date_range,
            "existing": bool(existing),
            "existing_value": existing_value_float,
        })

    return {"meters": meters}


# ====== Public endpoints (must be before dynamic routes) ======
@router.post("/public")
def create_readings_public(
    data: ReadingCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Public endpoint for testing."""
    try:
        # Получаем пользователя из сессии
        from ..models import User
        from ..security import get_user_id_from_session
        
        user_id = get_user_id_from_session(request)
        user = None
        if user_id:
            user = db.get(User, user_id)
            if user and user.is_active:
                pass  # Используем пользователя из сессии
            else:
                user = None
        
        # Fallback: если нет сессии, используем первого пользователя для теста
        if not user:
            user = db.query(User).first()
            if not user:
                raise HTTPException(status_code=500, detail="No user found in database")
        
        return create_readings_internal(data, user, db)
    except Exception as e:
        import traceback
        print(f"Error in create_readings_public: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ====== Create/Update readings ======
@router.post("/")
def create_readings(
    data: ReadingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upsert показаний за месяц.
    """
    return create_readings_internal(data, user, db)


def create_readings_internal(
    data: ReadingCreate,
    user: User,
    db: Session,
):
    """
    Internal function for creating/updating readings.
    """
    r = db.get(Resident, data.resident_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")

    try:
        reading_date = datetime.strptime(data.date_str, "%Y-%m-%d") if data.date_str else datetime.utcnow()
    except Exception:
        reading_date = datetime.utcnow()

    period_year = reading_date.year
    period_month = reading_date.month
    period_start = datetime(period_year, period_month, 1)
    period_end = datetime(period_year + (1 if period_month == 12 else 0), (1 if period_month == 12 else period_month + 1), 1)
    
    upserted: list[MeterReading] = []

    for it in data.items:
        meter_id = it.meter_id
        new_value_raw = it.new_value
        m = db.get(ResidentMeter, meter_id)
        if not m or m.resident_id != r.id:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Meter {meter_id} not found")

        # Для фикс-услуг (SERVICE, RENT, CONSTRUCTION) consumption всегда = 1
        is_fixed = m.meter_type in {MeterType.SERVICE, MeterType.RENT, MeterType.CONSTRUCTION}
        
        # Если new_value is None для фикс-услуги - удаляем существующую запись за месяц
        if is_fixed and new_value_raw is None:
            existing = (
                db.query(MeterReading)
                .filter(
                    MeterReading.resident_meter_id == m.id,
                    MeterReading.reading_date >= period_start,
                    MeterReading.reading_date < period_end,
                )
                .first()
            )
            if existing:
                # Удаляем строку инвойса
                db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == existing.id).delete()
                # Удаляем запись показания
                db.add(ReadingLog(
                    action="DELETE",
                    reading_id=existing.id,
                    resident_meter_id=m.id,
                    user_id=user.id,
                    details=f"deleted by unchecking fixed meter month={period_year}-{period_month:02d}",
                ))
                db.delete(existing)
            continue
        
        new_value = Decimal(str(new_value_raw))
        
        if is_fixed:
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            prev_val = Decimal(prev_rd.value) if prev_rd else Decimal("0")
            consumption = Decimal("1")
        else:
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            if prev_rd:
                prev_val = Decimal(prev_rd.value)
            else:
                prev_val = Decimal(m.initial_reading or 0)

            if new_value < prev_val:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"New value {new_value} is less than previous {prev_val}")

            consumption = new_value - prev_val

        # Ищем существующую запись за месяц
        existing = (
            db.query(MeterReading)
            .filter(
                MeterReading.resident_meter_id == m.id,
                MeterReading.reading_date >= period_start,
                MeterReading.reading_date < period_end,
            )
            .first()
        )

        tariff = db.get(Tariff, m.tariff_id)
        if not tariff:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Tariff {m.tariff_id} not found")

        # Расчёт суммы по тарифу
        amount_net, amount_vat, amount_total, steps_detail = compute_amount(consumption, tariff)

        if existing:
            # Обновляем существующую запись
            existing.value = new_value
            existing.consumption = consumption
            existing.amount_net = amount_net
            existing.amount_vat = amount_vat
            existing.amount_total = amount_total
            existing.note = data.note or existing.note
            db.flush()
            
            # Создаём лог для обновления
            db.add(ReadingLog(
                action="UPDATE",
                reading_id=existing.id,
                resident_meter_id=m.id,
                user_id=user.id,
                details=f"edit month={period_year}-{period_month:02d} new={float(new_value)} prev={float(prev_val)} cons={float(consumption)}",
            ))
            upserted.append(existing)
        else:
            # Создаём новую запись
            new_reading = MeterReading(
                resident_meter_id=m.id,
                reading_date=reading_date,
                value=new_value,
                consumption=consumption,
                tariff_id=tariff.id,
                amount_net=amount_net,
                vat_percent=tariff.vat_percent,
                amount_vat=amount_vat,
                amount_total=amount_total,
                note=data.note,
                created_by_id=user.id,
            )
            db.add(new_reading)
            db.flush()
            
            # Создаём лог для создания
            db.add(ReadingLog(
                action="CREATE",
                reading_id=new_reading.id,
                resident_meter_id=m.id,
                user_id=user.id,
                details=f"create month={period_year}-{period_month:02d} new={float(new_value)} prev={float(prev_val)} cons={float(consumption)}",
            ))
            upserted.append(new_reading)

        db.flush()

        # Обновляем/создаём строку инвойса
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.resident_id == r.id,
                Invoice.period_year == period_year,
                Invoice.period_month == period_month,
            )
            .first()
        )

        if not invoice:
            invoice = Invoice(
                resident_id=r.id,
                period_year=period_year,
                period_month=period_month,
                status=InvoiceStatus.DRAFT,
            )
            db.add(invoice)
            db.flush()

    # ВАЖНО: После обработки всех показаний из запроса, найдем ВСЕ показания за период
    # и убедимся, что для каждого есть строка в счете
    if upserted:
        # Определяем период из первого показания
        first_reading = upserted[0]
        period_year = first_reading.reading_date.year
        period_month = first_reading.reading_date.month
        resident_id = first_reading.resident_meter.resident_id
        
        from_dt = datetime(period_year, period_month, 1)
        to_dt = datetime(period_year + (1 if period_month == 12 else 0), (1 if period_month == 12 else period_month + 1), 1)
        
        # Найдем все показания за период для этого резидента
        all_period_readings = (
            db.query(MeterReading)
            .join(ResidentMeter, ResidentMeter.id == MeterReading.resident_meter_id)
            .filter(
                ResidentMeter.resident_id == resident_id,
                MeterReading.reading_date >= from_dt,
                MeterReading.reading_date < to_dt,
            )
            .all()
        )
        
        # Найдем счет за этот период
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.resident_id == resident_id,
                Invoice.period_year == period_year,
                Invoice.period_month == period_month,
            )
            .first()
        )
        
        if invoice:
            # Получим все существующие строки счета
            existing_lines = {line.meter_reading_id: line for line in db.query(InvoiceLine).filter(InvoiceLine.invoice_id == invoice.id).all() if line.meter_reading_id}
            
            # Создадим/обновим строки для всех показаний периода
            for rd in all_period_readings:
                if rd.id not in existing_lines:
                    # Создаем новую строку для показания, которого еще нет в счете
                    m = rd.resident_meter
                    meter_type_name = {
                        MeterType.ELECTRIC: "Электричество",
                        MeterType.GAS: "Газ",
                        MeterType.WATER: "Вода",
                        MeterType.SEWERAGE: "Канализация",
                        MeterType.SERVICE: "Сервис",
                        MeterType.RENT: "Аренда",
                        MeterType.CONSTRUCTION: "Строительство",
                    }.get(m.meter_type, "Услуга")
                    unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                            "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                    description = f"{meter_type_name} {float(rd.consumption)} {unit}"
                    
                    db.add(InvoiceLine(
                        invoice_id=invoice.id,
                        meter_reading_id=rd.id,
                        description=description,
                        amount_net=rd.amount_net,
                        amount_vat=rd.amount_vat,
                        amount_total=rd.amount_total,
                    ))
                else:
                    # Обновляем существующую строку
                    line = existing_lines[rd.id]
                    m = rd.resident_meter
                    meter_type_name = {
                        MeterType.ELECTRIC: "Электричество",
                        MeterType.GAS: "Газ",
                        MeterType.WATER: "Вода",
                        MeterType.SEWERAGE: "Канализация",
                        MeterType.SERVICE: "Сервис",
                        MeterType.RENT: "Аренда",
                        MeterType.CONSTRUCTION: "Строительство",
                    }.get(m.meter_type, "Услуга")
                    unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                            "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                    description = f"{meter_type_name} {float(rd.consumption)} {unit}"
                    line.description = description
                    line.amount_net = rd.amount_net
                    line.amount_vat = rd.amount_vat
                    line.amount_total = rd.amount_total
            
            # Пересчитываем итоги счёта после синхронизации всех строк
            db.flush()  # Важно: сохраняем все изменения перед пересчетом
            totals = db.query(
                func.coalesce(func.sum(InvoiceLine.amount_net), 0).label("net"),
                func.coalesce(func.sum(InvoiceLine.amount_vat), 0).label("vat"),
                func.coalesce(func.sum(InvoiceLine.amount_total), 0).label("total"),
            ).filter(InvoiceLine.invoice_id == invoice.id).first()

            if totals:
                invoice.amount_net = Decimal(str(totals.net or 0))
                invoice.amount_vat = Decimal(str(totals.vat or 0))
                invoice.amount_total = Decimal(str(totals.total or 0))

    db.commit()

    # Автораспределение аванса
    for rd in upserted:
        meter = db.get(ResidentMeter, rd.resident_meter_id)
        if meter:
            auto_apply_advance(db, meter.resident_id)

    return {"success": True, "upserted_count": len(upserted)}


# ====== Public endpoints (temporary for testing) ======
@router.get("/public")
def list_readings_public(
    db: Session = Depends(get_db),
    block_id: Optional[int] = Query(None),
    resident_id: Optional[int] = Query(None),
    meter_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    """Public endpoint for testing."""
    return list_readings(db, block_id, resident_id, meter_type, year, month, q, page, per_page)


@router.get("/resident/{resident_id}/meters/public")
def get_resident_meters_public(
    resident_id: int,
    db: Session = Depends(get_db),
    date: Optional[str] = Query(default=None),
):
    """Public endpoint for testing."""
    return get_resident_meters(resident_id, db, date)




# ====== Get detailed reading history for resident ======
@router.get("/resident/{resident_id}/history")
def get_reading_history(
    resident_id: int,
    db: Session = Depends(get_db),
    from_month: Optional[str] = Query(None, description="Начальный месяц в формате YYYY-MM"),
    to_month: Optional[str] = Query(None, description="Конечный месяц в формате YYYY-MM"),
):
    """
    Получить детальную историю показаний для резидента по всем счётчикам.
    Поддерживает фильтрацию по диапазону месяцев.
    """
    r = db.get(Resident, resident_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")

    meters = r.meters
    result = []
    
    # Парсим даты фильтрации по месяцам
    start_date = None
    end_date = None
    if from_month:
        try:
            year, month = map(int, from_month.split('-'))
            # Начало первого дня месяца
            start_date = datetime(year, month, 1)
        except (ValueError, AttributeError):
            pass
    
    if to_month:
        try:
            year, month = map(int, to_month.split('-'))
            # Конец последнего дня месяца (начало следующего месяца минус 1 секунда)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        except (ValueError, AttributeError):
            pass
    
    for m in meters:
        query = (
            db.query(MeterReading)
            .filter(MeterReading.resident_meter_id == m.id)
        )
        
        # Применяем фильтр по датам, если указан
        if start_date:
            query = query.filter(MeterReading.reading_date >= start_date)
        if end_date:
            query = query.filter(MeterReading.reading_date <= end_date)
        
        readings = (
            query.order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
            .all()
        )
        
        # Определяем тип для отображения
        if m.meter_type == MeterType.ELECTRIC:
            display_type = "Электричество"
            unit = "кВт·ч"
        elif m.meter_type == MeterType.GAS:
            display_type = "Газ"
            unit = "м³"
        elif m.meter_type == MeterType.WATER:
            display_type = "Вода"
            unit = "м³"
        elif m.meter_type == MeterType.SEWERAGE:
            display_type = "Канализация"
            unit = "м³"
        elif m.meter_type == MeterType.SERVICE:
            display_type = "Сервис"
            unit = "мес."
        elif m.meter_type == MeterType.RENT:
            display_type = "Аренда"
            unit = "мес."
        elif m.meter_type == MeterType.CONSTRUCTION:
            display_type = "Строительство"
            unit = "мес."
        else:
            display_type = "Неизвестно"
            unit = "—"
        
        readings_data = []
        for rd in readings:
            readings_data.append({
                "date": rd.reading_date.strftime("%Y-%m-%d"),
                "value": float(rd.value),
                "consumption": float(rd.consumption),
                "amount": float(rd.amount_total),
                "vat_percent": rd.vat_percent,
                "comment": rd.note or "—",
            })
        
        result.append({
            "meter_id": m.id,
            "type": display_type,
            "tariff_name": m.tariff.name if m.tariff else None,
            "serial_number": m.serial_number,
            "unit": unit,
            "readings": readings_data,
        })
    
    return {"meters": result}


@router.get("/resident/{resident_id}/history/public")
def get_reading_history_public(
    resident_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint for testing."""
    return get_reading_history(resident_id, db)


# ====== Delete last reading (public endpoint must be before main) ======
@router.delete("/meter/{meter_id}/last/public")
def delete_last_reading_public(
    meter_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Public endpoint for testing."""
    from ..models import User, ReadingLog, InvoiceLine, Invoice
    from ..security import get_user_id_from_session
    from sqlalchemy import func
    
    # Получаем пользователя из сессии
    user_id = get_user_id_from_session(request)
    user = None
    if user_id:
        user = db.get(User, user_id)
        if user and user.is_active:
            pass  # Используем пользователя из сессии
        else:
            user = None
    
    # Fallback: если нет сессии, используем первого пользователя для теста
    if not user:
        user = db.query(User).first()
        if not user:
            raise HTTPException(status_code=500, detail="No user found in database")
    
    m = db.get(ResidentMeter, meter_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meter not found")

    last = (
        db.query(MeterReading)
        .filter(MeterReading.resident_meter_id == m.id)
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
        .first()
    )
    if not last:
        return {"ok": True, "message": "Nothing to delete"}

    db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == last.id).delete()

    db.add(ReadingLog(
        action="DELETE",
        reading_id=last.id,
        resident_meter_id=m.id,
        user_id=user.id,
        details="deleted"
    ))
    db.delete(last)

    inv = db.query(Invoice).filter(
        Invoice.resident_id == m.resident_id,
        Invoice.period_year == last.reading_date.year,
        Invoice.period_month == last.reading_date.month,
    ).first()
    
    if inv:
        db.flush()
        sums = db.query(
            func.coalesce(func.sum(InvoiceLine.amount_net), 0),
            func.coalesce(func.sum(InvoiceLine.amount_vat), 0),
            func.coalesce(func.sum(InvoiceLine.amount_total), 0),
        ).filter(InvoiceLine.invoice_id == inv.id).one()

        inv.total_amount_net = Decimal(sums[0])
        inv.total_amount_vat = Decimal(sums[1])
        inv.total_amount_total = Decimal(sums[2])
        
        if inv.total_amount_total == 0:
            line_count = db.query(func.count(InvoiceLine.id)).filter(InvoiceLine.invoice_id == inv.id).scalar()
            if line_count == 0:
                db.delete(inv)

    db.commit()
    return {"ok": True, "message": "Last reading deleted successfully"}


@router.delete("/meter/{meter_id}/last")
def delete_last_reading(
    meter_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Удаляет последнее показание по счётчику.
    """
    from ..models import ReadingLog, InvoiceLine, Invoice
    from sqlalchemy import func
    
    m = db.get(ResidentMeter, meter_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meter not found")

    last = (
        db.query(MeterReading)
        .filter(MeterReading.resident_meter_id == m.id)
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
        .first()
    )
    if not last:
        return {"ok": True, "message": "Nothing to delete"}

    # Удаляем строку инвойса
    db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == last.id).delete()

    # Логируем удаление
    db.add(ReadingLog(
        action="DELETE",
        reading_id=last.id,
        resident_meter_id=m.id,
        user_id=user.id,
        details="deleted"
    ))
    db.delete(last)

    # Пересчитываем/удаляем инвойс периода
    inv = db.query(Invoice).filter(
        Invoice.resident_id == m.resident_id,
        Invoice.period_year == last.reading_date.year,
        Invoice.period_month == last.reading_date.month,
    ).first()
    
    if inv:
        db.flush()
        sums = db.query(
            func.coalesce(func.sum(InvoiceLine.amount_net), 0),
            func.coalesce(func.sum(InvoiceLine.amount_vat), 0),
            func.coalesce(func.sum(InvoiceLine.amount_total), 0),
        ).filter(InvoiceLine.invoice_id == inv.id).one()

        inv.total_amount_net = Decimal(sums[0])
        inv.total_amount_vat = Decimal(sums[1])
        inv.total_amount_total = Decimal(sums[2])
        
        if inv.total_amount_total == 0:
            # Проверяем, есть ли еще строки
            line_count = db.query(func.count(InvoiceLine.id)).filter(InvoiceLine.invoice_id == inv.id).scalar()
            if line_count == 0:
                db.delete(inv)

    db.commit()
    return {"ok": True, "message": "Last reading deleted successfully"}

