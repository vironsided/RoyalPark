# app/api/routers/residents.py
"""
Module: Residents management (CRUD + JSON for meters only)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-28

Purpose:
    Управление резидентами (без фикс-услуг). В каждой вилле могут быть счётчики:
      - ELECTRIC (кВт·ч)
      - GAS (м³)
      - WATER (м³)
      - SEWERAGE (м³, канализация)
      - SERVICE (Фикс цена из тарифа)
      - RENT (Фикс цена из тарифа)

    Возможности:
      - список с фильтрами
      - создание резидента + прикреплённые счётчики
      - редактирование (полная замена счётчиков)
      - удаление
      - JSON для модалки редактирования

Notes:
    - Фикс-услуги (тех. обслуживание, аренда) полностью исключены с бэкенда и фронта.
    - Все операции по счётчикам выполняются атомарно (commit/rollback).
    - Валидация входящих данных зеркалится с фронтом.
"""

from __future__ import annotations

from typing import Optional, List, Tuple
from decimal import Decimal, InvalidOperation
import json
import logging

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette import status

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import (
    User,
    RoleEnum,
    Block,
    Resident,
    ResidentStatus,
    ResidentType,
    CustomerType,
    ResidentMeter,
    MeterType,
    Tariff,
    MeterReading,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/residents", tags=["residents"])
templates = Jinja2Templates(directory="app/templates")


# ------------------------------ Helpers ------------------------------------- #

def _see_other(url: str) -> RedirectResponse:
    """Единый 303-редирект для завершения POST-операций."""
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def _to_decimal(value: object) -> Decimal:
    """Приведение к Decimal через str для избежания float-артефактов."""
    return Decimal(str(value))


def _parse_meters_json(raw: str) -> List[Tuple[MeterType, str, bool, Optional[Decimal], int]]:
    """
    Разбор JSON-массива счётчиков (БЕЗ фикс-услуг).

    Ожидаемый формат (строка JSON):
        [
          {
            "meter_type": "ELECTRIC"|"GAS"|"WATER"|"SEWERAGE"|"SERVICE"|"RENT",
            "serial": "AB123",
            "used": true|false,
            "initial": 0.0,            # обязателен если used=true, иначе игнорируется
            "tariff_id": 5
          },
          ...
        ]

    Возвращает список кортежей:
        (meter_type: MeterType, serial: str, used: bool, initial: Optional[Decimal], tariff_id: int)

    Ошибки -> ValueError("...") с кратким кодом.
    """
    try:
        data = json.loads(raw or "[]")
        assert isinstance(data, list)
    except Exception:
        raise ValueError("meters_invalid_json")

    result: List[Tuple[MeterType, str, bool, Optional[Decimal], int]] = []
    if not data:
        raise ValueError("meters_empty")

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"meters_item_{i}_not_object")

        mt = item.get("meter_type")
        serial = (item.get("serial") or "").strip()
        used = bool(item.get("used", False))
        initial_raw = item.get("initial", None)
        tariff_id = item.get("tariff_id")

        # meter_type
        if mt not in {m.value for m in MeterType}:
            raise ValueError(f"meters_item_{i}_bad_type")

        mtype = MeterType(mt)

        # serial (может быть пустым — если бизнес не требует, можно разрешить)
        # Если хочешь сделать обязательным — раскомментируй:
        # if not serial:
        #     raise ValueError(f"meters_item_{i}_empty_serial")

        # initial
        initial: Optional[Decimal] = None
        if used:
            try:
                initial = _to_decimal(initial_raw)
            except (InvalidOperation, Exception):
                raise ValueError(f"meters_item_{i}_bad_initial")
            if initial < 0:
                raise ValueError(f"meters_item_{i}_negative_initial")

        # tariff_id
        try:
            tariff_id = int(tariff_id)
        except Exception:
            raise ValueError(f"meters_item_{i}_bad_tariff")

        result.append((mtype, serial, used, initial, tariff_id))

    return result


# ------------------------------ Views --------------------------------------- #

@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def list_residents(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    block_id: Optional[int] = None,
    status: Optional[str] = None,      # ResidentStatus
    rtype: Optional[str] = None,       # ResidentType
    q: Optional[str] = None,           # unit/owner/phone/email
):
    """
    Страница списка резидентов с фильтрами и поиском.
    """
    blocks = db.execute(select(Block).order_by(Block.name.asc())).scalars().all()

    stmt = select(Resident)
    if block_id:
        stmt = stmt.where(Resident.block_id == block_id)
    if status in {s.value for s in ResidentStatus}:
        stmt = stmt.where(Resident.status == ResidentStatus(status))
    if rtype in {t.value for t in ResidentType}:
        stmt = stmt.where(Resident.resident_type == ResidentType(rtype))
    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Resident.unit_number).like(needle) |
            func.lower(Resident.owner_full_name).like(needle) |
            func.lower(Resident.owner_phone).like(needle) |
            func.lower(Resident.owner_email).like(needle)
        )

    residents = db.execute(stmt.order_by(Resident.id.asc())).scalars().all()

    # Все тарифы (для фронта) — отдадим id/name/type
    tariffs = db.execute(select(Tariff).order_by(Tariff.id.asc())).scalars().all()
    tariffs_simple = [
        {"id": t.id, "name": t.name, "meter_type": t.meter_type.value}
        for t in tariffs
    ]

    return templates.TemplateResponse(
        "residents.html",
        {
            "request": request,
            "user": user,
            "blocks": blocks,
            "residents": residents,
            "ResidentStatus": ResidentStatus,
            "ResidentType": ResidentType,
            "CustomerType": CustomerType,
            "MeterType": MeterType,
            "tariffs": tariffs_simple,
            "block_id": block_id or "",
            "status_val": status or "",
            "rtype_val": rtype or "",
            "q": q or "",
            "ok": request.query_params.get("ok"),
            "error": request.query_params.get("error"),
        },
    )


@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def create_resident(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    block_id: int = Form(...),
    unit_number: str = Form(...),
    resident_type: str = Form(...),
    customer_type: str = Form(...),
    status: str = Form(...),
    owner_full_name: str = Form(""),
    owner_phone: str = Form(""),
    owner_email: str = Form(""),
    meters_json: str = Form(...),
):
    """
    Создаёт резидента и прикрепляет счётчики (без фикс-услуг).
    """
    unit_number = (unit_number or "").strip()
    if not unit_number:
        return _see_other("/residents?error=empty_unit")

    if resident_type not in {t.value for t in ResidentType}:
        return _see_other("/residents?error=bad_rtype")
    if customer_type not in {c.value for c in CustomerType}:
        return _see_other("/residents?error=bad_ctype")
    if status not in {s.value for s in ResidentStatus}:
        return _see_other("/residents?error=bad_status")

    # Проверим блок
    blk = db.get(Block, block_id)
    if not blk:
        return _see_other("/residents?error=bad_block")

    # Разбор счётчиков
    try:
        meters = _parse_meters_json(meters_json)
    except ValueError as e:
        return _see_other(f"/residents?error={e}")

    # Уникальный номер дома в блоке
    exists = db.execute(
        select(Resident.id).where(
            Resident.block_id == block_id,
            func.lower(Resident.unit_number) == func.lower(unit_number),
        )
    ).first()
    if exists:
        return _see_other("/residents?error=exists")

    try:
        r = Resident(
            block_id=block_id,
            unit_number=unit_number,
            resident_type=ResidentType(resident_type),
            customer_type=CustomerType(customer_type),
            status=ResidentStatus(status),
            owner_full_name=(owner_full_name or "").strip(),
            owner_phone=(owner_phone or "").strip(),
            owner_email=(owner_email or "").strip(),
            created_by_id=user.id,
        )
        db.add(r)
        db.flush()  # нужен r.id

        # Вставляем счётчики
        for (mtype, serial, used, initial, tariff_id) in meters:
            # Проверим тариф и его тип
            t = db.get(Tariff, tariff_id)
            if not t or t.meter_type != mtype:
                raise ValueError("tariff_type_mismatch")

            db.add(
                ResidentMeter(
                    resident_id=r.id,
                    meter_type=mtype,
                    serial_number=serial,
                    initial_reading=(initial if (used and initial is not None) else 0),
                    tariff_id=tariff_id,
                    note=None,
                )
            )

        db.commit()
        logger.info("Resident created: id=%s unit=%r", r.id, r.unit_number)
        return _see_other("/residents?ok=created")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create resident: %s", exc)
        return _see_other("/residents?error=server")


@router.get(
    "/{resident_id}/json",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def get_resident_json(
    resident_id: int,
    db: Session = Depends(get_db),
):
    """
    Возвращает JSON для модалки редактирования.
    Флаг 'used' выводим из опорного значения: initial_reading > 0.
    """
    r: Optional[Resident] = db.get(Resident, resident_id)
    if not r:
        return JSONResponse({"error": "notfound"}, status_code=status.HTTP_404_NOT_FOUND)

    def to_used(m) -> bool:
        # initial_reading у тебя NOT NULL с дефолтом 0 — на всякий случай приводим к float
        try:
            return float(m.initial_reading or 0) > 0
        except Exception:
            return False

    def to_initial(m):
        # для фронта всегда число (0.0, если пусто/None)
        try:
            return float(m.initial_reading or 0)
        except Exception:
            return 0.0

    return {
        "id": r.id,
        "block_id": r.block_id,
        "unit_number": r.unit_number,
        "resident_type": r.resident_type.value,
        "customer_type": r.customer_type.value,
        "status": r.status.value,
        "owner_full_name": r.owner_full_name or "",
        "owner_phone": r.owner_phone or "",
        "owner_email": r.owner_email or "",
        "meters": [
            {
                "meter_type": m.meter_type.value,
                "serial": m.serial_number or "",
                "used": to_used(m),
                "initial": to_initial(m),
                "tariff_id": m.tariff_id,
            }
            for m in r.meters if m.is_active  # Только активные счётчики для редактирования
        ],
    }



@router.post(
    "/{resident_id}/update",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def update_resident(
    resident_id: int,
    db: Session = Depends(get_db),
    block_id: int = Form(...),
    unit_number: str = Form(...),
    resident_type: str = Form(...),
    customer_type: str = Form(...),
    status: str = Form(...),
    owner_full_name: str = Form(""),
    owner_phone: str = Form(""),
    owner_email: str = Form(""),
    meters_json: str = Form(...),
):
    """
    Полное обновление резидента и ПОЛНАЯ замена списка счётчиков.
    """
    r: Optional[Resident] = db.get(Resident, resident_id)
    if not r:
        return _see_other("/residents?error=notfound")

    unit_number = (unit_number or "").strip()
    if not unit_number:
        return _see_other("/residents?error=empty_unit")
    if resident_type not in {t.value for t in ResidentType}:
        return _see_other("/residents?error=bad_rtype")
    if customer_type not in {c.value for c in CustomerType}:
        return _see_other("/residents?error=bad_ctype")
    if status not in {s.value for s in ResidentStatus}:
        return _see_other("/residents?error=bad_status")

    # Проверим блок
    blk = db.get(Block, block_id)
    if not blk:
        return _see_other("/residents?error=bad_block")

    # Разбор счётчиков
    try:
        meters = _parse_meters_json(meters_json)
    except ValueError as e:
        return _see_other(f"/residents?error={e}")

    # Проверка уникальности unit_number в блоке (исключая текущую запись)
    exists = db.execute(
        select(Resident.id).where(
            Resident.id != r.id,
            Resident.block_id == block_id,
            func.lower(Resident.unit_number) == func.lower(unit_number),
        )
    ).first()
    if exists:
        return _see_other("/residents?error=exists")

    try:
        # Обновляем шапку
        r.block_id = block_id
        r.unit_number = unit_number
        r.resident_type = ResidentType(resident_type)
        r.customer_type = CustomerType(customer_type)
        r.status = ResidentStatus(status)
        r.owner_full_name = (owner_full_name or "").strip()
        r.owner_phone = (owner_phone or "").strip()
        r.owner_email = (owner_email or "").strip()

        # Умная замена счётчиков: сохраняем существующие с показаниями, обновляем/добавляем безопасно
        existing_meters_list = db.query(ResidentMeter).filter(ResidentMeter.resident_id == r.id).all()
        existing_meters = {m.id: m for m in existing_meters_list}
        
        # Проверяем, какие счётчики имеют показания (их нельзя удалять или изменять критичные поля)
        if existing_meters:
            meters_with_readings = {
                mid for (mid,) in db.query(MeterReading.resident_meter_id)
                .filter(MeterReading.resident_meter_id.in_(list(existing_meters.keys())))
                .distinct()
                .all()
            }
        else:
            meters_with_readings = set()
        
        # Сопоставляем новые счётчики со старыми (только те, у которых нет показаний)
        matched_meter_ids = set()
        
        for (mtype, serial, used, initial, tariff_id) in meters:
            t = db.get(Tariff, tariff_id)
            if not t or t.meter_type != mtype:
                raise ValueError("tariff_type_mismatch")

            matching_meter = None
            serial_clean = (serial or "").strip()
            initial_clean = (initial if (used and initial is not None) else 0)
            
            # Находим все кандидаты для сопоставления (без показаний, не сопоставленные)
            # Разделяем на активные и неактивные для приоритизации
            active_candidates = [
                em for em in existing_meters_list
                if (em.id not in matched_meter_ids and 
                    em.id not in meters_with_readings and
                    em.is_active and
                    em.meter_type == mtype and 
                    em.tariff_id == tariff_id)
            ]
            inactive_candidates = [
                em for em in existing_meters_list
                if (em.id not in matched_meter_ids and 
                    em.id not in meters_with_readings and
                    not em.is_active and
                    em.meter_type == mtype and 
                    em.tariff_id == tariff_id)
            ]
            
            # Стратегия сопоставления (приоритет активным):
            # 1. Если есть серийный номер - сопоставляем строго по нему (сначала среди активных)
            # 2. Если серийного нет - сопоставляем по initial_reading (сначала среди активных)
            # 3. Если не сопоставили - сопоставляем только если есть ровно один кандидат (активный или неактивный)
            # 4. Иначе создаём новый (предотвращаем дубликаты)
            
            if serial_clean:
                # Строгое сопоставление по серийному номеру (приоритет активным)
                for em in active_candidates:
                    if (em.serial_number or "").strip() == serial_clean:
                        matching_meter = em
                        break
                if not matching_meter:
                    for em in inactive_candidates:
                        if (em.serial_number or "").strip() == serial_clean:
                            matching_meter = em
                            break
            else:
                # Для счётчиков без серийного номера (фикс-услуги)
                # Сопоставляем по initial_reading, если оно указано (приоритет активным)
                if initial_clean > 0:
                    for em in active_candidates:
                        if abs(float(em.initial_reading or 0) - float(initial_clean)) < 0.0001:
                            matching_meter = em
                            break
                    if not matching_meter:
                        for em in inactive_candidates:
                            if abs(float(em.initial_reading or 0) - float(initial_clean)) < 0.0001:
                                matching_meter = em
                                break
                
                # Если не сопоставили по initial_reading, сопоставляем только если есть ровно один кандидат
                if not matching_meter:
                    all_candidates = active_candidates + inactive_candidates
                    if len(all_candidates) == 1:
                        matching_meter = all_candidates[0]
                # Если кандидатов больше одного и не сопоставили - не сопоставляем (создадим новый)
                # Это предотвращает создание дубликатов при удалении других счётчиков
            
            if matching_meter:
                # Обновляем существующий счётчик (без показаний - безопасно)
                matching_meter.serial_number = serial_clean
                matching_meter.initial_reading = initial_clean
                matching_meter.is_active = True
                matched_meter_ids.add(matching_meter.id)
            else:
                # Перед созданием нового проверяем, нет ли уже такого же счётчика
                # (защита от дубликатов - проверяем все счётчики, не только активные)
                duplicate_check = db.query(ResidentMeter).filter(
                    ResidentMeter.resident_id == r.id,
                    ResidentMeter.meter_type == mtype,
                    ResidentMeter.tariff_id == tariff_id,
                )
                if serial_clean:
                    duplicate_check = duplicate_check.filter(ResidentMeter.serial_number == serial_clean)
                else:
                    duplicate_check = duplicate_check.filter(
                        (ResidentMeter.serial_number == None) | (ResidentMeter.serial_number == '')
                    )
                
                existing_duplicate = duplicate_check.first()
                if existing_duplicate:
                    # Если нашли дубликат - обновляем его вместо создания нового
                    if existing_duplicate.id not in matched_meter_ids:
                        existing_duplicate.serial_number = serial_clean
                        existing_duplicate.initial_reading = initial_clean
                        existing_duplicate.is_active = True
                        matched_meter_ids.add(existing_duplicate.id)
                        logger.info(f"Reactivated existing meter instead of creating duplicate: id={existing_duplicate.id}")
                    else:
                        logger.warning(f"Skipping duplicate meter: already matched id={existing_duplicate.id}")
                    continue
                
                # Создаём новый счётчик только если не нашли подходящий для обновления
                new_meter = ResidentMeter(
                    resident_id=r.id,
                    meter_type=mtype,
                    serial_number=serial_clean,
                    initial_reading=initial_clean,
                    tariff_id=tariff_id,
                    note=None,
                    is_active=True,
                )
                db.add(new_meter)
        
        # Обрабатываем несоответствующие существующие счётчики
        for meter_id, meter in existing_meters.items():
            if meter_id not in matched_meter_ids:
                if meter_id in meters_with_readings:
                    # Счётчики с показаниями оставляем, но деактивируем
                    meter.is_active = False
                else:
                    # Счётчики без показаний можно безопасно удалить
                    db.delete(meter)

        db.commit()
        logger.info("Resident updated: id=%s unit=%r", r.id, r.unit_number)
        return _see_other("/residents?ok=updated")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update resident id=%s: %s", resident_id, exc)
        return _see_other("/residents?error=server")


@router.post(
    "/{resident_id}/delete",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def delete_resident(
    resident_id: int,
    db: Session = Depends(get_db),
):
    """
    Удаляет резидента (и счётчики — если в БД FK настроен каскад; иначе нужно удалять их вручную).
    """
    r: Optional[Resident] = db.get(Resident, resident_id)
    if not r:
        return _see_other("/residents?error=notfound")

    try:
        db.delete(r)
        db.commit()
        logger.info("Resident deleted: id=%s unit=%r", r.id, r.unit_number)
        return _see_other("/residents?ok=deleted")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete resident id=%s: %s", resident_id, exc)
        return _see_other("/residents?error=server")
