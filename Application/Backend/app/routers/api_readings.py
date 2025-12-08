from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

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

    readings_q = readings_q.filter(
        MeterReading.reading_date >= from_dt,
        MeterReading.reading_date < to_dt,
    )
    period_readings = readings_q.all()
    
    # Логирование для отладки
    print(f"[DEBUG] Period: {from_dt} to {to_dt}")
    print(f"[DEBUG] Found {len(period_readings)} readings")

    # Агрегат по счётчикам
    rows: dict[int, dict] = {}
    print(f"[DEBUG] Processing {len(period_readings)} readings")
    for rd in period_readings:
        meter = rd.resident_meter
        res_id = meter.resident_id
        print(f"[DEBUG] Reading: resident_id={res_id}, meter_id={meter.id}, meter_type={meter.meter_type}, is_active={meter.is_active}, date={rd.reading_date}")

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

    return {
        "blocks": [{"id": b.id, "name": b.name} for b in blocks],
        "residents": [{"id": r.id, "unit_number": r.unit_number, "block_name": r.block.name if r.block else ""} for r in residents],
        "rows": result_rows,
        "year": year,
        "month": month,
        "total_amount": float(sum(r["total_amount"] for r in result_rows)),
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
            print(f"DEBUG: get_resident_meters - date={date}, period_start={period_start}, period_end={period_end}")
        except Exception as e:
            print(f"DEBUG: get_resident_meters - failed to parse date '{date}': {e}")
            period_start = period_end = None

    meters_list = db.query(ResidentMeter).filter(
        ResidentMeter.resident_id == resident_id,
        ResidentMeter.is_active == True  # Показываем только активные счётчики
    ).options(
        joinedload(ResidentMeter.tariff).joinedload(Tariff.steps)
    ).all()
    
    meters = []
    for m in meters_list:
        # prev_value: ПОСЛЕДНЯЯ запись ДО начала месяца (или initial)
        if period_start:
            # Проверим все показания для этого счетчика для отладки
            all_readings = db.query(MeterReading).filter(MeterReading.resident_meter_id == m.id).order_by(MeterReading.reading_date.desc()).all()
            print(f"DEBUG: Meter ID={m.id}, type={m.meter_type.value}, resident_id={m.resident_id}, all readings count={len(all_readings)}")
            for rd in all_readings[:5]:  # Показываем первые 5 для отладки
                is_before = rd.reading_date < period_start
                print(f"DEBUG:   - Reading ID={rd.id}, date={rd.reading_date}, value={rd.value}, is_before_period={is_before} (period_start={period_start})")
            
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            if prev_rd:
                prev_value = Decimal(prev_rd.value)
                print(f"DEBUG: Meter ID={m.id}, type={m.meter_type.value}, ✓ found prev_rd: date={prev_rd.reading_date}, value={prev_rd.value}, prev_value={prev_value}")
            else:
                prev_value = Decimal(m.initial_reading or 0)
                print(f"DEBUG: Meter ID={m.id}, type={m.meter_type.value}, ✗ no prev_rd (period_start={period_start}), using initial_reading={m.initial_reading}, prev_value={prev_value}")
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
                print(f"DEBUG: Meter ID={m.id}, type={m.meter_type.value}, found last_any: date={last_any.reading_date}, value={last_any.value}, prev_value={prev_value}")
            else:
                prev_value = Decimal(m.initial_reading or 0)
                print(f"DEBUG: Meter ID={m.id}, type={m.meter_type.value}, no last_any, using initial_reading={m.initial_reading}, prev_value={prev_value}")

        existing = None
        if period_start and period_end:
            existing = (
                db.query(MeterReading)
                .filter(
                    MeterReading.resident_meter_id == m.id,
                    MeterReading.reading_date >= period_start,
                    MeterReading.reading_date < period_end,
                )
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )

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
        if m.meter_type == MeterType.CONSTRUCTION and m.tariff.steps:
            first_step = m.tariff.steps[0]
            if first_step.from_date and first_step.to_date:
                date_range = {
                    "from_date": first_step.from_date.isoformat(),
                    "to_date": first_step.to_date.isoformat(),
                }

        # Подготовка данных о тарифе для расчета суммы на frontend
        tariff_steps = []
        if m.tariff.steps:
            for step in sorted(m.tariff.steps, key=lambda s: s.from_value or 0):
                tariff_steps.append({
                    "from_value": float(step.from_value) if step.from_value is not None else None,
                    "to_value": float(step.to_value) if step.to_value is not None else None,
                    "from_date": step.from_date.isoformat() if step.from_date else None,
                    "to_date": step.to_date.isoformat() if step.to_date else None,
                    "price": float(step.price),
                })
        
        prev_value_float = float(prev_value)
        existing_value_float = float(existing.value) if existing else None
        
        print(f"DEBUG: Final meter data: ID={m.id}, type={display_type}, tariff={m.tariff.name}, prev_value={prev_value_float}, existing_value={existing_value_float}, unit={unit}, initial_reading={m.initial_reading}")
        
        meters.append({
            "meter_id": m.id,
            "type": m.meter_type.value,
            "display_type": display_type,
            "serial": m.serial_number,
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name,
            "vat_percent": m.tariff.vat_percent,
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
    db: Session = Depends(get_db),
):
    """Public endpoint for testing."""
    try:
        # Create a dummy user for public endpoint
        from ..models import User
        dummy_user = db.query(User).first()
        if not dummy_user:
            raise HTTPException(status_code=500, detail="No user found in database")
        return create_readings_internal(data, dummy_user, db)
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
    
    print(f"DEBUG POST: create_readings_internal - date_str={data.date_str}, reading_date={reading_date}, period_start={period_start}, period_end={period_end}, resident_id={data.resident_id}")

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
            # Проверим все показания для этого счетчика для отладки
            all_readings_post = db.query(MeterReading).filter(MeterReading.resident_meter_id == m.id).order_by(MeterReading.reading_date.desc()).all()
            print(f"DEBUG POST: Meter ID={m.id}, type={m.meter_type.value}, period_start={period_start}, all readings count={len(all_readings_post)}")
            for rd in all_readings_post[:5]:  # Показываем первые 5 для отладки
                is_before = rd.reading_date < period_start
                print(f"DEBUG POST:   - Reading ID={rd.id}, date={rd.reading_date}, value={rd.value}, is_before_period={is_before}")
            
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            if prev_rd:
                prev_val = Decimal(prev_rd.value)
                print(f"DEBUG POST: Meter ID={m.id}, ✓ found prev_rd: date={prev_rd.reading_date}, value={prev_rd.value}, prev_val={prev_val}")
            else:
                prev_val = Decimal(m.initial_reading or 0)
                print(f"DEBUG POST: Meter ID={m.id}, ✗ no prev_rd, using initial_reading={m.initial_reading}, prev_val={prev_val}")

            print(f"DEBUG POST: Meter ID={m.id}, new_value={new_value}, prev_val={prev_val}, comparison: {new_value < prev_val}")
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
            )
            db.add(new_reading)
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

        # Обновляем/создаём строку инвойса для этого счётчика
        line = (
            db.query(InvoiceLine)
            .filter(
                InvoiceLine.invoice_id == invoice.id,
                InvoiceLine.meter_reading_id == (existing.id if existing else None),
            )
            .first()
        )

        # Формируем описание для строки инвойса
        meter_type_name = {
            MeterType.ELECTRIC: "Электричество",
            MeterType.GAS: "Газ",
            MeterType.WATER: "Вода",
            MeterType.SEWERAGE: "Канализация",
            MeterType.SERVICE: "Сервис",
            MeterType.RENT: "Аренда",
            MeterType.CONSTRUCTION: "Строительство",
        }.get(m.meter_type, "Услуга")
        
        description = f"{meter_type_name} - {m.tariff.name if m.tariff else 'Без тарифа'}"
        
        if line and existing:
            line.meter_reading_id = existing.id
            line.description = description
            line.amount_net = amount_net
            line.amount_vat = amount_vat
            line.amount_total = amount_total
        else:
            if line:
                db.delete(line)
            new_line = InvoiceLine(
                invoice_id=invoice.id,
                meter_reading_id=upserted[-1].id,
                description=description,
                amount_net=amount_net,
                amount_vat=amount_vat,
                amount_total=amount_total,
            )
            db.add(new_line)

        # Пересчитываем итоги счёта
        totals = db.query(
            func.sum(InvoiceLine.amount_net).label("net"),
            func.sum(InvoiceLine.amount_vat).label("vat"),
            func.sum(InvoiceLine.amount_total).label("total"),
        ).filter(InvoiceLine.invoice_id == invoice.id).first()

        if totals:
            invoice.amount_net = totals.net or Decimal("0")
            invoice.amount_vat = totals.vat or Decimal("0")
            invoice.amount_total = totals.total or Decimal("0")

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
):
    """Public endpoint for testing."""
    return list_readings(db, block_id, resident_id, meter_type, year, month, q)


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
):
    """
    Получить детальную историю показаний для резидента по всем счётчикам.
    """
    r = db.get(Resident, resident_id)
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")

    meters = r.meters
    result = []
    
    for m in meters:
        readings = (
            db.query(MeterReading)
            .filter(MeterReading.resident_meter_id == m.id)
            .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
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
    db: Session = Depends(get_db),
):
    """Public endpoint for testing."""
    from ..models import User
    dummy_user = db.query(User).first()
    if not dummy_user:
        raise HTTPException(status_code=500, detail="No user found in database")
    
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

    db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == last.id).delete()

    db.add(ReadingLog(
        action="DELETE",
        reading_id=last.id,
        resident_meter_id=m.id,
        user_id=dummy_user.id,
        details="deleted via public API"
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
        details="deleted via API"
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

