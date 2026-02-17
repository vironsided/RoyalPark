# app/api/routers/readings.py
"""
Module: Readings (list, detail, modal helpers, create/update per month, delete-last)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-30

What changed:
  - Единственная запись в месяц на счётчик (upsert): если запись за месяц есть — обновляем её,
    а не создаём вторую (правильный перерасчёт расхода и сумм).
  - База для расхода — ПРЕДЫДУЩЕЕ показание ДО начала месяца (или initial при его отсутствии).
  - Инвойс-строка для счётчика за месяц обновляется, затем итоги счёта пересчитываются SQL-агрегацией.
  - /resident/{resident_id}/meters умеет принимать ?date=YYYY-MM-DD, чтобы показывать «режим редактирования»:
      * prev_value → значение до начала месяца,
      * existing → есть ли запись в месяце,
      * existing_value → значение записи (для подстановки в модалку).
  - SERVICE/RENT: в режиме редактирования чекбокс изначально включён, если запись уже есть (cons=1).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import json

from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from starlette import status


from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import (
    User, RoleEnum,
    Block, Resident, ResidentMeter, MeterType,
    Tariff, CustomerType,
    MeterReading, ReadingLog,
    Invoice, InvoiceLine, InvoiceStatus,
)
from .payments import auto_apply_advance  # авторспределение аванса


router = APIRouter(prefix="/readings", tags=["readings"])
templates = Jinja2Templates(directory="app/templates")


# ====== расчёт по ступеням тарифа (вынесено в API-роутер) ======
# Бизнес-логика расчёта (включая stable_tariff) находится в `api_readings.py`.
from .api_readings import money, compute_amount, get_gas_annual_prev  # noqa: E402


def _upsert_auto_sewerage_line_for_invoice(
    db: Session,
    inv: Invoice,
    all_period_readings: list[MeterReading],
) -> None:
    """
    Канализация как % от воды.

    Правила:
    - Если есть реальные показания SEWERAGE в периоде — авто-строку НЕ добавляем (и удаляем, если была).
    - Процент берём из WATER-тарифа (Tariff.sewerage_percent), применяем ПО КАЖДОМУ water-reading.
    - Для INDIVIDUAL (физ.лицо): сумма воды делится — Вода = (1-p) * вода, Канализация = p * вода (итог не меняется).
    - Для LEGAL (юр.лицо): канализация добавляется сверху — Канализация = p * вода (итог увеличивается).
    - Авто-строка имеет meter_reading_id = NULL и description начинается с "Канализация".
    """
    if not inv or not inv.id:
        return

    readings = all_period_readings or []

    # Если в периоде есть реальные начисления канализации — автостроку удаляем и выходим
    has_real_sewerage = any(
        (rd.resident_meter and rd.resident_meter.meter_type == MeterType.SEWERAGE)
        for rd in readings
    )

    auto_line = (
        db.query(InvoiceLine)
        .filter(
            InvoiceLine.invoice_id == inv.id,
            InvoiceLine.meter_reading_id.is_(None),
            InvoiceLine.description.ilike("Канализация%"),
        )
        .first()
    )

    if has_real_sewerage:
        # восстанавливаем воду как есть (на случай, если раньше делили)
        for rd in readings:
            if rd.resident_meter and rd.resident_meter.meter_type == MeterType.WATER:
                line = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id, InvoiceLine.meter_reading_id == rd.id).first()
                if line:
                    line.amount_net = money(Decimal(str(rd.amount_net or 0)))
                    line.amount_vat = money(Decimal(str(rd.amount_vat or 0)))
                    line.amount_total = money(Decimal(str(rd.amount_total or 0)))
                    line.description = f"Вода {float(Decimal(str(rd.consumption or 0)))} м³"
        if auto_line:
            db.delete(auto_line)
        return

    water_readings = [
        rd for rd in readings
        if rd.resident_meter and rd.resident_meter.meter_type == MeterType.WATER
    ]
    if not water_readings:
        if auto_line:
            db.delete(auto_line)
        return

    sew_net = Decimal("0")
    sew_vat = Decimal("0")
    sew_total = Decimal("0")
    water_cons = Decimal("0")
    sewer_cons = Decimal("0")

    for rd in water_readings:
        water_cons += Decimal(str(rd.consumption or 0))

        # линия воды в счёте
        line = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id, InvoiceLine.meter_reading_id == rd.id).first()
        if not line:
            continue

        base_net = money(Decimal(str(rd.amount_net or 0)))
        base_vat = money(Decimal(str(rd.amount_vat or 0)))
        base_total = money(Decimal(str(rd.amount_total or 0)))

        t = db.get(Tariff, rd.tariff_id) if rd.tariff_id else None
        percent = Decimal(str(getattr(t, "sewerage_percent", 0) or 0))
        if percent <= 0:
            # если % не задан — вода как есть
            line.amount_net = base_net
            line.amount_vat = base_vat
            line.amount_total = base_total
            line.description = f"Вода {float(Decimal(str(rd.consumption or 0)))} м³"
            continue

        k = percent / Decimal("100")

        # Режим выбираем по типу WATER тарифа (а не по resident.customer_type):
        # - INDIVIDUAL: делим сумму воды (вода уменьшается)
        # - LEGAL: добавляем канализацию сверху
        consumption = Decimal(str(rd.consumption or 0))
        if getattr(t, "customer_type", None) == CustomerType.INDIVIDUAL:
            # делим сумму воды: вода = (1-k), канализация = k (итог не меняется)
            new_net = money(base_net * (Decimal("1") - k))
            new_vat = money(base_vat * (Decimal("1") - k))
            new_total = money(base_total * (Decimal("1") - k))

            line.amount_net = new_net
            line.amount_vat = new_vat
            line.amount_total = new_total

            sew_net += (base_net - new_net)
            sew_vat += (base_vat - new_vat)
            sew_total += (base_total - new_total)
            water_display_cons = consumption * (Decimal("1") - k)
            sewer_display_cons = consumption * k
            line.description = f"Вода {float(water_display_cons)} м³"
            sewer_cons += sewer_display_cons
        else:
            # LEGAL: вода как есть, канализация сверху
            line.amount_net = base_net
            line.amount_vat = base_vat
            line.amount_total = base_total

            sew_net += money(base_net * k)
            sew_vat += money(base_vat * k)
            sew_total += money(base_total * k)
            line.description = f"Вода {float(consumption)} м³"
            sewer_cons += consumption * k

    if sew_total <= 0:
        if auto_line:
            db.delete(auto_line)
        return

    desc = f"Канализация  {float(sewer_cons)} м³"

    if auto_line:
        auto_line.description = desc
        auto_line.amount_net = money(sew_net)
        auto_line.amount_vat = money(sew_vat)
        auto_line.amount_total = money(sew_total)
    else:
        db.add(InvoiceLine(
            invoice_id=inv.id,
            meter_reading_id=None,
            description=desc,
            amount_net=money(sew_net),
            amount_vat=money(sew_vat),
            amount_total=money(sew_total),
        ))


# ====== Страницы ======
@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def list_readings(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    block_id: str | None = None,
    resident_id: str | None = None,
    meter_type: str | None = None,
    year: int | None = None,
    month: int | None = None,
    q: str | None = None,
):
    """
    Список показаний за выбранный месяц (агрегировано по резидентам и их счётчикам).
    """
    blocks = db.query(Block).order_by(Block.name.asc()).all()

    # Выпадашка резидентов (по блоку/поиску)
    residents_q = db.query(Resident).order_by(Resident.unit_number.asc())
    if block_id and block_id.strip():
        try:
            residents_q = residents_q.filter(Resident.block_id == int(block_id))
        except ValueError:
            pass
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
    readings_q = db.query(MeterReading).join(ResidentMeter).join(Resident)
    if block_id and block_id.strip():
        try:
            readings_q = readings_q.filter(Resident.block_id == int(block_id))
        except ValueError:
            pass
    if resident_id and resident_id.strip():
        try:
            readings_q = readings_q.filter(Resident.id == int(resident_id))
        except ValueError:
            pass
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
        mrow["total"]       += Decimal(rd.amount_total)

    paid_resident_ids = set(
        rid for (rid,) in db.query(Resident.id)
        .join(Invoice, Invoice.resident_id == Resident.id)
        .filter(
            Invoice.period_year == year,
            Invoice.period_month == month,
            Invoice.status == InvoiceStatus.PAID
        ).all()
    )

    return templates.TemplateResponse("readings.html", {
        "request": request,
        "user": user,
        "blocks": blocks,
        "residents": residents,
        "rows": rows,
        "period_readings": period_readings,
        "meter_type": meter_type or "",
        "block_id": block_id or "",
        "resident_id": resident_id or "",
        "year": year,
        "month": month,
        "q": q or "",
        "MeterType": MeterType,
        "paid_resident_ids": list(paid_resident_ids),  # передаём как список для Jinja
    })


@router.get(
    "/detail/{resident_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def readings_detail(
    resident_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    История показаний по каждому счётчику резидента (новые сверху).
    """
    r = db.get(Resident, resident_id)
    if not r:
        return RedirectResponse(url="/readings?error=resident_notfound", status_code=302)

    meters = r.meters
    history = {}
    for m in meters:
        recs = (
            db.query(MeterReading)
            .filter(MeterReading.resident_meter_id == m.id)
            .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
            .all()
        )
        history[m.id] = recs

    return templates.TemplateResponse("readings_detail.html", {
        "request": request,
        "user": user,
        "resident": r,
        "meters": meters,
        "history": history,
    })


# ====== AJAX-помощники ======
@router.get("/resident/{resident_id}/meters")
def get_resident_meters(
    resident_id: int,
    db: Session = Depends(get_db),
    date: str | None = Query(default=None, description="YYYY-MM-DD для режима редактирования"),
):
    """
    Данные для модалки: список счётчиков резидента.
    Если ?date задан, считаем, что редактируем этот месяц:
      - prev_value — значение ПОСЛЕДНЕЙ записи ДО начала месяца (или initial),
      - existing/existing_value — запись в месяце (если есть).
    Для SERVICE/RENT выставляем is_fixed = True и единицы = "мес.".
    """
    r = db.get(Resident, resident_id)
    if not r:
        return JSONResponse({"error": "notfound"}, status_code=404)

    period_start = period_end = None
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            period_start = datetime(d.year, d.month, 1)
            period_end = datetime(d.year + (1 if d.month == 12 else 0), (1 if d.month == 12 else d.month + 1), 1)
        except Exception:
            period_start = period_end = None

    # Загружаем тарифы со ступенями для CONSTRUCTION
    meters_list = db.query(ResidentMeter).filter(
        ResidentMeter.resident_id == resident_id
    ).options(
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
            prev_value = Decimal(prev_rd.value) if prev_rd else Decimal(m.initial_reading or 0)
        else:
            # без даты — просто последнее показание
            last_any = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            prev_value = Decimal(last_any.value) if last_any else Decimal(m.initial_reading or 0)

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
            # Берем первый шаг (для CONSTRUCTION обычно один шаг с датами)
            first_step = m.tariff.steps[0]
            if first_step.from_date and first_step.to_date:
                date_range = {
                    "from_date": first_step.from_date.isoformat(),
                    "to_date": first_step.to_date.isoformat(),
                }

        meters.append({
            "meter_id": m.id,
            "type": m.meter_type.value,
            "display_type": display_type,
            "serial": m.serial_number,
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name,
            "vat_percent": m.tariff.vat_percent,
            "prev_value": float(prev_value),
            "unit": unit,
            "is_fixed": is_fixed,
            "date_range": date_range,  # Для CONSTRUCTION: {from_date, to_date}
            # для редактирования:
            "existing": bool(existing),
            "existing_value": (float(existing.value) if existing else None),
        })

    return {"meters": meters}


# ====== Создание/редактирование за месяц (idempotent per meter-month) ======
@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def create_readings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    resident_id: int = Form(...),
    date_str: str = Form(""),
    payload_json: str = Form(...),
    note: str = Form(""),
):
    """
    Upsert показаний за месяц:
      - если запись в месяце есть → обновляем её,
      - иначе создаём.
    База для расхода — показание ДО начала месяца (или initial).
    """
    r = db.get(Resident, resident_id)
    if not r:
        return RedirectResponse(url="/readings?error=resident_notfound", status_code=302)

    try:
        items = json.loads(payload_json); assert isinstance(items, list)
    except Exception:
        return RedirectResponse(url="/readings?error=bad_payload", status_code=302)

    try:
        reading_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()
    except Exception:
        reading_date = datetime.utcnow()

    period_year = reading_date.year
    period_month = reading_date.month
    period_start = datetime(period_year, period_month, 1)
    period_end = datetime(period_year + (1 if period_month == 12 else 0), (1 if period_month == 12 else period_month + 1), 1)

    upserted: list[MeterReading] = []

    for it in items:
        meter_id = int(it.get("meter_id"))
        new_value_raw = it.get("new_value")
        m = db.get(ResidentMeter, meter_id)
        if not m or m.resident_id != r.id:
            db.rollback()
            return RedirectResponse(url="/readings?error=meter_notfound", status_code=302)

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
            continue  # Пропускаем создание/обновление для этого счётчика
        
        new_value = Decimal(str(new_value_raw))
        
        if is_fixed:
            # Для фикс-услуг: consumption = 1, prev_val = последнее значение до месяца (или 0)
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            prev_val = Decimal(prev_rd.value) if prev_rd else Decimal("0")
            consumption = Decimal("1")  # всегда 1 для фикс-услуг
        else:
            # Для обычных счётчиков: prev = последняя запись ДО начала месяца или initial
            prev_rd = (
                db.query(MeterReading)
                .filter(MeterReading.resident_meter_id == m.id, MeterReading.reading_date < period_start)
                .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
                .first()
            )
            prev_val = Decimal(prev_rd.value) if prev_rd else Decimal(m.initial_reading or 0)

            if new_value < prev_val:
                db.rollback()
                return RedirectResponse(url="/readings?error=value_less_prev", status_code=302)

            consumption = new_value - prev_val

        t = db.get(Tariff, m.tariff_id)
        annual_prev = get_gas_annual_prev(db, m.id, period_start) if m.meter_type == MeterType.GAS else None
        net, vat, total, _ = compute_amount(consumption, t, annual_prev=annual_prev)

        # запись за этот месяц (если есть)
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

        if existing:
            # --- UPDATE ---
            existing.reading_date = reading_date
            existing.value = new_value
            existing.consumption = consumption
            existing.tariff_id = t.id
            existing.vat_percent = t.vat_percent
            existing.amount_net = net
            existing.amount_vat = vat
            existing.amount_total = total
            existing.note = note or None
            db.flush()

            # строка инвойса под этот reading
            line = db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == existing.id).first()
            if not line:
                # если строки не было — создадим
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                desc = f"{title} {float(consumption)} {unit}"
                db.add(InvoiceLine(
                    invoice_id=None,  # выставим чуть ниже, когда возьмём inv.id
                    meter_reading_id=existing.id,
                    description=desc,
                    amount_net=net, amount_vat=vat, amount_total=total,
                ))
            else:
                # обновим сумму/описание
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                line.description = f"{title} {float(consumption)} {unit}"
                line.amount_net = net; line.amount_vat = vat; line.amount_total = total

            db.add(ReadingLog(
                action="UPDATE",
                reading_id=existing.id,
                resident_meter_id=m.id,
                user_id=user.id,
                details=f"edit month={period_year}-{period_month:02d} new={float(new_value)} prev={float(prev_val)} cons={float(consumption)}",
            ))
            upserted.append(existing)

        else:
            # --- INSERT ---
            rd = MeterReading(
                resident_meter_id=m.id,
                reading_date=reading_date,
                value=new_value,
                consumption=consumption,
                tariff_id=t.id,
                vat_percent=t.vat_percent,
                amount_net=net,
                amount_vat=vat,
                amount_total=total,
                note=note or None,
                created_by_id=user.id,
            )
            db.add(rd); db.flush()
            upserted.append(rd)

            db.add(ReadingLog(
                action="CREATE",
                reading_id=rd.id,
                resident_meter_id=m.id,
                user_id=user.id,
                details=f"create month={period_year}-{period_month:02d} new={float(new_value)} prev={float(prev_val)} cons={float(consumption)}",
            ))

    # инвойс за период (создадим при необходимости + авто-номер)
    # Только если есть чтения для добавления/обновления
    inv = None
    if upserted:
        inv = db.query(Invoice).filter(
            Invoice.resident_id == r.id,
            Invoice.period_year == period_year,
            Invoice.period_month == period_month,
        ).first()
        if not inv:
            inv = Invoice(
                resident_id=r.id,
                period_year=period_year,
                period_month=period_month,
                created_by_id=user.id,
            )
            db.add(inv); db.flush()

            if not inv.number:
                prefix = f"{inv.period_year}-{inv.period_month:02d}"
                last_num = (
                    db.query(Invoice.number)
                    .filter(Invoice.period_year == inv.period_year,
                            Invoice.period_month == inv.period_month,
                            Invoice.number.ilike(f"{prefix}/%"))
                    .order_by(Invoice.number.desc()).first()
                )
                if last_num and last_num[0]:
                    try:
                        seq = int(last_num[0].split("/")[-1]) + 1
                    except Exception:
                        seq = inv.id
                else:
                    seq = 1
                inv.number = f"{prefix}/{seq:06d}"
    else:
        # Если только удаления - найдём существующий инвойс для пересчёта
        inv = db.query(Invoice).filter(
            Invoice.resident_id == r.id,
            Invoice.period_year == period_year,
            Invoice.period_month == period_month,
        ).first()

    # привести строки инвойса в соответствие (на случай UPDATE)
    if inv:
        # Сначала обработаем текущие показания из запроса
        for rd in upserted:
            # найти/создать строку под этот reading
            line = db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == rd.id).first()
            if not line:
                # INSERT был выше, но про запас…
                m = rd.resident_meter
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                db.add(InvoiceLine(
                    invoice_id=inv.id,
                    meter_reading_id=rd.id,
                    description=f"{title} {float(rd.consumption)} {unit}",
                    amount_net=rd.amount_net,
                    amount_vat=rd.amount_vat,
                    amount_total=rd.amount_total,
                ))
            else:
                # обновляем существующую строку
                m = rd.resident_meter
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                line.invoice_id = inv.id
                line.description = f"{title} {float(rd.consumption)} {unit}"
                line.amount_net = rd.amount_net
                line.amount_vat = rd.amount_vat
                line.amount_total = rd.amount_total

        # ВАЖНО: Найдем ВСЕ показания за этот период для этого резидента
        # и убедимся, что для каждого есть строка в счете
        from_dt = datetime(period_year, period_month, 1)
        to_dt = datetime(period_year + (1 if period_month == 12 else 0), (1 if period_month == 12 else period_month + 1), 1)
        
        all_period_readings = (
            db.query(MeterReading)
            .join(ResidentMeter, ResidentMeter.id == MeterReading.resident_meter_id)
            .filter(
                ResidentMeter.resident_id == r.id,
                MeterReading.reading_date >= from_dt,
                MeterReading.reading_date < to_dt,
            )
            .all()
        )
        
        # Получим все существующие строки счета
        existing_lines = {line.meter_reading_id: line for line in db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all() if line.meter_reading_id}
        
        # Создадим/обновим строки для всех показаний периода
        for rd in all_period_readings:
            if rd.id not in existing_lines:
                # Создаем новую строку для показания, которого еще нет в счете
                m = rd.resident_meter
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                db.add(InvoiceLine(
                    invoice_id=inv.id,
                    meter_reading_id=rd.id,
                    description=f"{title} {float(rd.consumption)} {unit}",
                    amount_net=rd.amount_net,
                    amount_vat=rd.amount_vat,
                    amount_total=rd.amount_total,
                ))
            else:
                # Обновляем существующую строку, если данные изменились
                line = existing_lines[rd.id]
                m = rd.resident_meter
                unit = ("кВт·ч" if m.meter_type == MeterType.ELECTRIC else
                        "м³" if m.meter_type in {MeterType.GAS, MeterType.WATER, MeterType.SEWERAGE} else "мес.")
                title = ("Электричество" if m.meter_type == MeterType.ELECTRIC else
                         "Газ" if m.meter_type == MeterType.GAS else
                         "Вода" if m.meter_type == MeterType.WATER else
                         "Канализация" if m.meter_type == MeterType.SEWERAGE else
                         "Сервис" if m.meter_type == MeterType.SERVICE else
                         "Аренда" if m.meter_type == MeterType.RENT else
                         "Строительство")
                line.description = f"{title} {float(rd.consumption)} {unit}"
                line.amount_net = rd.amount_net
                line.amount_vat = rd.amount_vat
                line.amount_total = rd.amount_total

        # --- АВТО: Канализация как % от воды (если настроено в WATER тарифе) ---
        _upsert_auto_sewerage_line_for_invoice(db, inv, all_period_readings)

        # --- ПЕРЕСЧЁТ ИТОГОВ СЧЁТА по фактическим строкам в БД ---
        db.flush()  # Важно: сохраняем все изменения перед пересчетом
        sums = db.query(
            func.coalesce(func.sum(InvoiceLine.amount_net), 0),
            func.coalesce(func.sum(InvoiceLine.amount_vat), 0),
            func.coalesce(func.sum(InvoiceLine.amount_total), 0),
        ).filter(InvoiceLine.invoice_id == inv.id).one()
        inv.amount_net = Decimal(str(sums[0] or 0))
        inv.amount_vat = Decimal(str(sums[1] or 0))
        inv.amount_total = Decimal(str(sums[2] or 0))
        
        # Если счёт пустой (все показания удалены) - удаляем его
        if inv.amount_total == 0 and not db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).first():
            db.delete(inv)

    db.commit()

    # --- НОВОЕ: сразу применим аванс (если у резидента есть свободные остатки) ---
    try:
        applied_cnt = auto_apply_advance(db, r.id)
        if applied_cnt:
            db.commit()
    except Exception:
        # не мешаем основному флоу записи показаний из-за проблем с автораскладкой
        db.rollback()

    return RedirectResponse(url="/readings?ok=created", status_code=302)


# ====== Удаление последнего чтения ======
@router.post(
    "/delete-last",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def delete_last_reading(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    meter_id: int = Form(...),
):
    """
    Удаляет последнее показание по счётчику и соответствующую строку из счета периода.
    """
    ajax = request.headers.get("x-requested-with") == "fetch"

    m = db.get(ResidentMeter, meter_id)
    if not m:
        if ajax:
            return JSONResponse({"ok": False, "error": "meter_notfound"}, status_code=400)
        return RedirectResponse(url="/readings?error=meter_notfound", status_code=302)

    last = (
        db.query(MeterReading)
        .filter(MeterReading.resident_meter_id == m.id)
        .order_by(MeterReading.reading_date.desc(), MeterReading.id.desc())
        .first()
    )
    if not last:
        if ajax:
            return JSONResponse({"ok": False, "error": "nothing_to_delete"}, status_code=200)
        return RedirectResponse(url="/readings?error=nothing_to_delete", status_code=302)

    # удалить строку счета
    db.query(InvoiceLine).filter(InvoiceLine.meter_reading_id == last.id).delete()

    db.add(ReadingLog(action="DELETE", reading_id=last.id, resident_meter_id=m.id, user_id=user.id, details="deleted"))
    db.delete(last)

    # пересчитать/удалить инвойс периода
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

        inv.amount_net = Decimal(sums[0]); inv.amount_vat = Decimal(sums[1]); inv.amount_total = Decimal(sums[2])
        if inv.amount_total == 0 and not inv.lines:
            db.delete(inv)

    db.commit()
    if ajax:
        return JSONResponse({"ok": True})
    return RedirectResponse(url="/readings?ok=deleted", status_code=302)


# ====== Онлайновый расчёт суммы ======
@router.get("/quote")
def quote(tariff_id: int, qty: float, db: Session = Depends(get_db)):
    t = db.get(Tariff, tariff_id)
    if not t:
        return JSONResponse({"error": "tariff_notfound"}, status_code=404)
    net, vat, total, breakdown = compute_amount(Decimal(str(qty)), t)
    return {
        "amount_net": float(net),
        "amount_vat": float(vat),
        "amount_total": float(total),
        "vat_percent": t.vat_percent,
        "breakdown": breakdown,
    }
