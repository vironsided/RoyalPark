from typing import List, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..database import get_db
from ..models import (
    User, RoleEnum, Block, Resident, ResidentMeter,
    ResidentType, ResidentStatus, CustomerType, MeterType, Tariff
)
from ..deps import get_current_user


router = APIRouter(prefix="/api/residents", tags=["residents-api"])


# Pydantic models
class MeterIn(BaseModel):
    meter_type: str  # MeterType value
    serial: str
    used: bool  # True если initial_reading > 0
    initial: float  # initial_reading
    tariff_id: int


class ResidentOut(BaseModel):
    id: int
    block_id: int
    block_name: Optional[str] = None
    unit_number: str
    resident_type: str
    customer_type: str
    status: str
    owner_full_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    comment: Optional[str] = None
    meters: List[dict] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResidentCreate(BaseModel):
    block_id: int
    unit_number: str
    resident_type: str  # ResidentType value
    customer_type: str  # CustomerType value
    status: str  # ResidentStatus value
    owner_full_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    comment: Optional[str] = None
    meters: List[MeterIn] = []


class ResidentUpdate(BaseModel):
    block_id: Optional[int] = None
    unit_number: Optional[str] = None
    resident_type: Optional[str] = None
    customer_type: Optional[str] = None
    status: Optional[str] = None
    owner_full_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    comment: Optional[str] = None
    meters: Optional[List[MeterIn]] = None


def _parse_meters(meters_data: List[MeterIn]) -> List[dict]:
    """Валидация и преобразование счётчиков."""
    result = []
    fixed_price_types = {MeterType.SERVICE, MeterType.RENT, MeterType.CONSTRUCTION}
    
    for m in meters_data:
        if m.meter_type not in {t.value for t in MeterType}:
            raise ValueError(f"Invalid meter_type: {m.meter_type}")
        
        meter_type_enum = MeterType(m.meter_type)
        is_fixed_price = meter_type_enum in fixed_price_types
        
        # Для фикс-услуг серийный номер не обязателен (может быть "-" или пустым)
        # Для обычных счётчиков серийный номер обязателен
        serial = m.serial.strip()
        if not is_fixed_price and not serial:
            raise ValueError("Serial number is required for non-fixed-price meters")
        
        # Если серийный номер пустой для фикс-услуги, используем "-"
        if is_fixed_price and not serial:
            serial = "-"
        
        if m.initial < 0:
            raise ValueError("Initial reading cannot be negative")
        
        result.append({
            "meter_type": meter_type_enum,
            "serial": serial,
            "initial_reading": Decimal(str(m.initial)),
            "tariff_id": m.tariff_id,
        })
    return result


@router.get("/", response_model=List[ResidentOut])
def list_residents_api(
    db: Session = Depends(get_db),
    block_id: Optional[int] = None,
    status: Optional[str] = None,
    rtype: Optional[str] = None,
    q: Optional[str] = None,
    actor: User = Depends(get_current_user),
):
    """
    JSON-список резидентов с фильтрами.
    """
    stmt = select(Resident)
    
    if block_id:
        stmt = stmt.where(Resident.block_id == block_id)
    if status and status in {s.value for s in ResidentStatus}:
        stmt = stmt.where(Resident.status == ResidentStatus(status))
    if rtype and rtype in {t.value for t in ResidentType}:
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
    
    result = []
    for r in residents:
        meters_data = []
        for m in r.meters:
            # В списке резидентов показываем только активные счётчики
            if m.is_active:
                meters_data.append({
                    "id": m.id,
                    "meter_type": m.meter_type.value,
                    "serial_number": m.serial_number,
                    "initial_reading": float(m.initial_reading),
                    "tariff_id": m.tariff_id,
                    "tariff_name": m.tariff.name if m.tariff else None,
                    "is_active": m.is_active,
                })
        
        result.append({
            "id": r.id,
            "block_id": r.block_id,
            "block_name": r.block.name if r.block else None,
            "unit_number": r.unit_number,
            "resident_type": r.resident_type.value,
            "customer_type": r.customer_type.value,
            "status": r.status.value,
            "owner_full_name": r.owner_full_name,
            "owner_phone": r.owner_phone,
            "owner_email": r.owner_email,
            "comment": r.comment,
            "meters": meters_data,
            "created_at": r.created_at,
        })
    
    return result


# ВРЕМЕННО: endpoint без авторизации для теста
@router.get("/public", response_model=List[ResidentOut])
def list_residents_public(
    db: Session = Depends(get_db),
    block_id: Optional[int] = None,
    status: Optional[str] = None,
    rtype: Optional[str] = None,
    q: Optional[str] = None,
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    stmt = select(Resident)
    
    if block_id:
        stmt = stmt.where(Resident.block_id == block_id)
    if status and status in {s.value for s in ResidentStatus}:
        stmt = stmt.where(Resident.status == ResidentStatus(status))
    if rtype and rtype in {t.value for t in ResidentType}:
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
    
    result = []
    for r in residents:
        meters_data = []
        for m in r.meters:
            # В списке резидентов показываем только активные счётчики
            if m.is_active:
                meters_data.append({
                    "id": m.id,
                    "meter_type": m.meter_type.value,
                    "serial_number": m.serial_number,
                    "initial_reading": float(m.initial_reading),
                    "tariff_id": m.tariff_id,
                    "tariff_name": m.tariff.name if m.tariff else None,
                    "is_active": m.is_active,
                })
        
        result.append({
            "id": r.id,
            "block_id": r.block_id,
            "block_name": r.block.name if r.block else None,
            "unit_number": r.unit_number,
            "resident_type": r.resident_type.value,
            "customer_type": r.customer_type.value,
            "status": r.status.value,
            "owner_full_name": r.owner_full_name,
            "owner_phone": r.owner_phone,
            "owner_email": r.owner_email,
            "comment": r.comment,
            "meters": meters_data,
            "created_at": r.created_at,
        })
    
    return result


@router.post("/", response_model=ResidentOut, status_code=status.HTTP_201_CREATED)
def create_resident_api(
    payload: ResidentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Создание нового резидента.
    """
    # Валидация блока
    block = db.get(Block, payload.block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Валидация типов
    if payload.resident_type not in {t.value for t in ResidentType}:
        raise HTTPException(status_code=400, detail=f"Invalid resident_type: {payload.resident_type}")
    if payload.customer_type not in {c.value for c in CustomerType}:
        raise HTTPException(status_code=400, detail=f"Invalid customer_type: {payload.customer_type}")
    if payload.status not in {s.value for s in ResidentStatus}:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    
    # Проверка уникальности unit_number в блоке
    existing = db.execute(
        select(Resident.id).where(
            Resident.block_id == payload.block_id,
            Resident.unit_number == payload.unit_number.strip()
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Unit number already exists in this block")
    
    # Разбор счётчиков
    try:
        meters_data = _parse_meters(payload.meters) if payload.meters else []
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Проверка тарифов для счётчиков
    for m_data in meters_data:
        tariff = db.get(Tariff, m_data["tariff_id"])
        if not tariff:
            raise HTTPException(status_code=404, detail=f"Tariff {m_data['tariff_id']} not found")
        if tariff.meter_type != m_data["meter_type"]:
            raise HTTPException(
                status_code=400,
                detail=f"Tariff {m_data['tariff_id']} meter_type mismatch"
            )
    
    # Создание резидента
    resident = Resident(
        block_id=payload.block_id,
        unit_number=payload.unit_number.strip(),
        resident_type=ResidentType(payload.resident_type),
        customer_type=CustomerType(payload.customer_type),
        status=ResidentStatus(payload.status),
        owner_full_name=payload.owner_full_name.strip() if payload.owner_full_name else None,
        owner_phone=payload.owner_phone.strip() if payload.owner_phone else None,
        owner_email=payload.owner_email.strip() if payload.owner_email else None,
        comment=payload.comment.strip() if payload.comment else None,
        created_by_id=actor.id,
    )
    db.add(resident)
    db.flush()
    
    # Создание счётчиков
    for m_data in meters_data:
        meter = ResidentMeter(
            resident_id=resident.id,
            meter_type=m_data["meter_type"],
            serial_number=m_data["serial"],
            initial_reading=m_data["initial_reading"],
            tariff_id=m_data["tariff_id"],
            is_active=True,
        )
        db.add(meter)
    
    db.commit()
    db.refresh(resident)
    
    # Формирование ответа - показываем только активные счетчики
    meters_data = []
    seen_meter_ids = set()
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


# ВРЕМЕННО: endpoint без авторизации для теста
@router.post("/public", response_model=ResidentOut, status_code=status.HTTP_201_CREATED)
def create_resident_public(
    payload: ResidentCreate,
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    # Валидация блока
    block = db.get(Block, payload.block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    # Валидация типов
    if payload.resident_type not in {t.value for t in ResidentType}:
        raise HTTPException(status_code=400, detail=f"Invalid resident_type: {payload.resident_type}")
    if payload.customer_type not in {c.value for c in CustomerType}:
        raise HTTPException(status_code=400, detail=f"Invalid customer_type: {payload.customer_type}")
    if payload.status not in {s.value for s in ResidentStatus}:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    
    # Проверка уникальности unit_number в блоке
    existing = db.execute(
        select(Resident.id).where(
            Resident.block_id == payload.block_id,
            Resident.unit_number == payload.unit_number.strip()
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Unit number already exists in this block")
    
    # Разбор счётчиков
    try:
        meters_data = _parse_meters(payload.meters) if payload.meters else []
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Проверка тарифов для счётчиков
    for m_data in meters_data:
        tariff = db.get(Tariff, m_data["tariff_id"])
        if not tariff:
            raise HTTPException(status_code=404, detail=f"Tariff {m_data['tariff_id']} not found")
        if tariff.meter_type != m_data["meter_type"]:
            raise HTTPException(
                status_code=400,
                detail=f"Tariff {m_data['tariff_id']} meter_type mismatch"
            )
    
    # Создание резидента
    resident = Resident(
        block_id=payload.block_id,
        unit_number=payload.unit_number.strip(),
        resident_type=ResidentType(payload.resident_type),
        customer_type=CustomerType(payload.customer_type),
        status=ResidentStatus(payload.status),
        owner_full_name=payload.owner_full_name.strip() if payload.owner_full_name else None,
        owner_phone=payload.owner_phone.strip() if payload.owner_phone else None,
        owner_email=payload.owner_email.strip() if payload.owner_email else None,
        comment=payload.comment.strip() if payload.comment else None,
        created_by_id=None,
    )
    db.add(resident)
    db.flush()
    
    # Создание счётчиков
    for m_data in meters_data:
        meter = ResidentMeter(
            resident_id=resident.id,
            meter_type=m_data["meter_type"],
            serial_number=m_data["serial"],
            initial_reading=m_data["initial_reading"],
            tariff_id=m_data["tariff_id"],
            is_active=True,
        )
        db.add(meter)
    
    db.commit()
    db.refresh(resident)
    
    # Формирование ответа - показываем только активные счетчики
    meters_data = []
    seen_meter_ids = set()
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


@router.get("/{resident_id}", response_model=ResidentOut)
def get_resident_api(
    resident_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Получение данных резидента для редактирования.
    """
    from sqlalchemy.orm import selectinload
    
    # Загружаем резидента - используем selectinload для избежания дубликатов
    resident = db.query(Resident).options(selectinload(Resident.meters)).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    # Теперь resident.meters не должен содержать дубликатов благодаря selectinload
    # Но оставляем проверку на всякий случай
    seen_meter_ids = set()
    meters_data = []
    
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов от старых неактивных)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID (на случай, если они все еще есть)
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


# ВРЕМЕННО: endpoint без авторизации для теста
@router.get("/{resident_id}/public", response_model=ResidentOut)
def get_resident_public(
    resident_id: int,
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    from sqlalchemy.orm import selectinload
    
    # Загружаем резидента - используем selectinload для избежания дубликатов
    resident = db.query(Resident).options(selectinload(Resident.meters)).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    # Теперь resident.meters не должен содержать дубликатов благодаря selectinload
    # Но оставляем проверку на всякий случай
    seen_meter_ids = set()
    meters_data = []
    
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов от старых неактивных)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID (на случай, если они все еще есть)
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


@router.put("/{resident_id}", response_model=ResidentOut)
def update_resident_api(
    resident_id: int,
    payload: ResidentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Обновление резидента (полная замена счётчиков).
    """
    resident = db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    # Обновление полей
    if payload.block_id is not None:
        block = db.get(Block, payload.block_id)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        resident.block_id = payload.block_id
    
    if payload.unit_number is not None:
        unit_number = payload.unit_number.strip()
        if not unit_number:
            raise HTTPException(status_code=400, detail="Unit number cannot be empty")
        # Проверка уникальности (исключая текущую запись)
        existing = db.execute(
            select(Resident.id).where(
                Resident.id != resident.id,
                Resident.block_id == resident.block_id,
                Resident.unit_number == unit_number
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Unit number already exists in this block")
        resident.unit_number = unit_number
    
    if payload.resident_type is not None:
        if payload.resident_type not in {t.value for t in ResidentType}:
            raise HTTPException(status_code=400, detail=f"Invalid resident_type: {payload.resident_type}")
        resident.resident_type = ResidentType(payload.resident_type)
    
    if payload.customer_type is not None:
        if payload.customer_type not in {c.value for c in CustomerType}:
            raise HTTPException(status_code=400, detail=f"Invalid customer_type: {payload.customer_type}")
        resident.customer_type = CustomerType(payload.customer_type)
    
    if payload.status is not None:
        if payload.status not in {s.value for s in ResidentStatus}:
            raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
        resident.status = ResidentStatus(payload.status)
    
    if payload.owner_full_name is not None:
        resident.owner_full_name = payload.owner_full_name.strip() if payload.owner_full_name else None
    if payload.owner_phone is not None:
        resident.owner_phone = payload.owner_phone.strip() if payload.owner_phone else None
    if payload.owner_email is not None:
        resident.owner_email = payload.owner_email.strip() if payload.owner_email else None
    if payload.comment is not None:
        resident.comment = payload.comment.strip() if payload.comment else None
    
    # Полная замена счётчиков
    if payload.meters is not None:
        # Удаляем старые активные счётчики физически из базы
        # Это предотвращает накопление дубликатов
        from ..models import ResidentMeter
        db.query(ResidentMeter).filter(
            ResidentMeter.resident_id == resident.id,
            ResidentMeter.is_active == True
        ).delete(synchronize_session=False)
        
        # Разбор новых счётчиков
        try:
            meters_data = _parse_meters(payload.meters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Проверка тарифов
        for m_data in meters_data:
            tariff = db.get(Tariff, m_data["tariff_id"])
            if not tariff:
                raise HTTPException(status_code=404, detail=f"Tariff {m_data['tariff_id']} not found")
            if tariff.meter_type != m_data["meter_type"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tariff {m_data['tariff_id']} meter_type mismatch"
                )
        
        # Создание новых счётчиков
        for m_data in meters_data:
            meter = ResidentMeter(
                resident_id=resident.id,
                meter_type=m_data["meter_type"],
                serial_number=m_data["serial"],
                initial_reading=m_data["initial_reading"],
                tariff_id=m_data["tariff_id"],
                is_active=True,
            )
            db.add(meter)
    
    db.commit()
    db.refresh(resident)
    
    # Формирование ответа - показываем только активные счетчики
    meters_data = []
    seen_meter_ids = set()
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


# ВРЕМЕННО: endpoint без авторизации для теста
@router.put("/{resident_id}/public", response_model=ResidentOut)
def update_resident_public(
    resident_id: int,
    payload: ResidentUpdate,
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    resident = db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    # Обновление полей
    if payload.block_id is not None:
        block = db.get(Block, payload.block_id)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        resident.block_id = payload.block_id
    
    if payload.unit_number is not None:
        unit_number = payload.unit_number.strip()
        if not unit_number:
            raise HTTPException(status_code=400, detail="Unit number cannot be empty")
        # Проверка уникальности (исключая текущую запись)
        existing = db.execute(
            select(Resident.id).where(
                Resident.id != resident.id,
                Resident.block_id == resident.block_id,
                Resident.unit_number == unit_number
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Unit number already exists in this block")
        resident.unit_number = unit_number
    
    if payload.resident_type is not None:
        if payload.resident_type not in {t.value for t in ResidentType}:
            raise HTTPException(status_code=400, detail=f"Invalid resident_type: {payload.resident_type}")
        resident.resident_type = ResidentType(payload.resident_type)
    
    if payload.customer_type is not None:
        if payload.customer_type not in {c.value for c in CustomerType}:
            raise HTTPException(status_code=400, detail=f"Invalid customer_type: {payload.customer_type}")
        resident.customer_type = CustomerType(payload.customer_type)
    
    if payload.status is not None:
        if payload.status not in {s.value for s in ResidentStatus}:
            raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
        resident.status = ResidentStatus(payload.status)
    
    if payload.owner_full_name is not None:
        resident.owner_full_name = payload.owner_full_name.strip() if payload.owner_full_name else None
    if payload.owner_phone is not None:
        resident.owner_phone = payload.owner_phone.strip() if payload.owner_phone else None
    if payload.owner_email is not None:
        resident.owner_email = payload.owner_email.strip() if payload.owner_email else None
    if payload.comment is not None:
        resident.comment = payload.comment.strip() if payload.comment else None
    
    # Полная замена счётчиков
    if payload.meters is not None:
        # Удаляем старые активные счётчики физически из базы
        # Это предотвращает накопление дубликатов
        from ..models import ResidentMeter
        db.query(ResidentMeter).filter(
            ResidentMeter.resident_id == resident.id,
            ResidentMeter.is_active == True
        ).delete(synchronize_session=False)
        
        # Разбор новых счётчиков
        try:
            meters_data = _parse_meters(payload.meters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Проверка тарифов
        for m_data in meters_data:
            tariff = db.get(Tariff, m_data["tariff_id"])
            if not tariff:
                raise HTTPException(status_code=404, detail=f"Tariff {m_data['tariff_id']} not found")
            if tariff.meter_type != m_data["meter_type"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tariff {m_data['tariff_id']} meter_type mismatch"
                )
        
        # Создание новых счётчиков
        for m_data in meters_data:
            meter = ResidentMeter(
                resident_id=resident.id,
                meter_type=m_data["meter_type"],
                serial_number=m_data["serial"],
                initial_reading=m_data["initial_reading"],
                tariff_id=m_data["tariff_id"],
                is_active=True,
            )
            db.add(meter)
    
    db.commit()
    db.refresh(resident)
    
    # Формирование ответа - показываем только активные счетчики
    meters_data = []
    seen_meter_ids = set()
    for m in resident.meters:
        # Показываем только активные счетчики (чтобы избежать дубликатов)
        if not m.is_active:
            continue
        # Пропускаем дубликаты по ID
        if m.id in seen_meter_ids:
            continue
        seen_meter_ids.add(m.id)
        
        meters_data.append({
            "id": m.id,
            "meter_type": m.meter_type.value,
            "serial_number": m.serial_number,
            "initial_reading": float(m.initial_reading),
            "tariff_id": m.tariff_id,
            "tariff_name": m.tariff.name if m.tariff else None,
            "is_active": m.is_active,
        })
    
    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "owner_full_name": resident.owner_full_name,
        "owner_phone": resident.owner_phone,
        "owner_email": resident.owner_email,
        "comment": resident.comment,
        "meters": meters_data,
        "created_at": resident.created_at,
    }


@router.delete("/{resident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resident_api(
    resident_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Удаление резидента.
    """
    resident = db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    db.delete(resident)
    db.commit()
    return None


# ВРЕМЕННО: endpoint без авторизации для теста
@router.delete("/{resident_id}/public", status_code=status.HTTP_204_NO_CONTENT)
def delete_resident_public(
    resident_id: int,
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    resident = db.get(Resident, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    db.delete(resident)
    db.commit()
    return None

