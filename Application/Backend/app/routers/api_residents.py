from typing import List, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..database import get_db
from ..models import (
    User, RoleEnum, Block, Resident, ResidentMeter,
    ResidentType, ResidentStatus, CustomerType, MeterType, Tariff, MeterReading,
    Invoice, InvoiceLine, InvoiceStatus, PaymentApplication
)
from ..deps import get_current_user


router = APIRouter(prefix="/api/residents", tags=["residents-api"])


# Pydantic models
class MeterIn(BaseModel):
    id: Optional[int] = None  # existing ResidentMeter.id (optional; helps avoid losing history)
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
    debt: Optional[float] = 0.0  # начальный долг (если задан)
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
    debt: Optional[float] = 0.0  # начальный долг (до внедрения системы)
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
    debt: Optional[float] = None  # обновление начального долга (opening invoice)
    meters: Optional[List[MeterIn]] = None


def _opening_invoice_number(resident_id: int) -> str:
    return f"OPEN/{resident_id:06d}"


def _get_opening_invoice(db: Session, resident_id: int) -> Invoice | None:
    """Ищем инвойс начального долга по стабильному номеру OPEN/{resident_id}."""
    return (
        db.execute(
            select(Invoice)
            .where(
                Invoice.resident_id == resident_id,
                Invoice.number == _opening_invoice_number(resident_id),
            )
            .order_by(Invoice.id.desc())
        )
        .scalars()
        .first()
    )


def _get_opening_debt(db: Session, resident_id: int) -> Decimal:
    """Возвращает сумму начального долга (0, если его нет или он отменён)."""
    inv = _get_opening_invoice(db, resident_id)
    if not inv or inv.status == InvoiceStatus.CANCELED:
        return Decimal("0")
    return Decimal(str(inv.amount_total or 0))


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
            "id": m.id,
            "meter_type": meter_type_enum,
            "serial": serial,
            "initial_reading": Decimal(str(m.initial)),
            "tariff_id": m.tariff_id,
        })
    return result


def _list_residents_internal(
    db: Session,
    block_id: Optional[int] = None,
    status: Optional[str] = None,
    rtype: Optional[str] = None,
    q: Optional[str] = None,
    unit_number: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
):
    """Внутренняя функция для получения списка резидентов (без авторизации)."""
    stmt = select(Resident)
    
    if block_id:
        stmt = stmt.where(Resident.block_id == block_id)
    if status and status in {s.value for s in ResidentStatus}:
        stmt = stmt.where(Resident.status == ResidentStatus(status))
    if rtype and rtype in {t.value for t in ResidentType}:
        stmt = stmt.where(Resident.resident_type == ResidentType(rtype))
    if unit_number:
        unit_number = unit_number.strip()
        if "-" in unit_number:
            parts = unit_number.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    # Для диапазонов пытаемся привести unit_number к числу в БД
                    # Используем CAST если возможно, или просто сравниваем строки если нет
                    # Но лучше всего для "101-105" просто искать по диапазону чисел
                    # Мы будем использовать cast к INTEGER для unit_number если это возможно
                    stmt = stmt.where(
                        func.cast(Resident.unit_number, func.Integer).between(start, end)
                    )
                except (ValueError, Exception):
                    # Если не удалось распарсить как числа, используем LIKE
                    stmt = stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))
            else:
                stmt = stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))
        else:
            # Для одиночного номера используем или точное совпадение или префикс
            stmt = stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))
            
    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Resident.unit_number).like(needle) |
            func.lower(Resident.owner_full_name).like(needle) |
            func.lower(Resident.owner_phone).like(needle) |
            func.lower(Resident.owner_email).like(needle)
        )
    
    # Подсчет общего количества
    count_stmt = select(func.count(Resident.id))
    if block_id:
        count_stmt = count_stmt.where(Resident.block_id == block_id)
    if status and status in {s.value for s in ResidentStatus}:
        count_stmt = count_stmt.where(Resident.status == ResidentStatus(status))
    if rtype and rtype in {t.value for t in ResidentType}:
        count_stmt = count_stmt.where(Resident.resident_type == ResidentType(rtype))
    
    # Дублируем логику фильтрации для count_stmt
    if unit_number:
        unit_number = unit_number.strip()
        if "-" in unit_number:
            parts = unit_number.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    count_stmt = count_stmt.where(
                        func.cast(Resident.unit_number, func.Integer).between(start, end)
                    )
                except (ValueError, Exception):
                    count_stmt = count_stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))
            else:
                count_stmt = count_stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))
        else:
            count_stmt = count_stmt.where(Resident.unit_number.ilike(f"%{unit_number}%"))

    if q:
        needle = f"%{q.strip().lower()}%"
        count_stmt = count_stmt.where(
            func.lower(Resident.unit_number).like(needle) |
            func.lower(Resident.owner_full_name).like(needle) |
            func.lower(Resident.owner_phone).like(needle) |
            func.lower(Resident.owner_email).like(needle)
        )
    
    total = db.execute(count_stmt).scalar() or 0
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page
    
    # Применяем пагинацию
    residents = db.execute(
        stmt.order_by(Resident.id.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()
    
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
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "last_page": last_page,
    }


@router.get("/")
def list_residents_api(
    db: Session = Depends(get_db),
    block_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    rtype: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    unit_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    actor: User = Depends(get_current_user),
):
    """
    JSON-список резидентов с фильтрами и пагинацией.
    """
    return _list_residents_internal(
        db=db,
        block_id=block_id,
        status=status,
        rtype=rtype,
        q=q,
        unit_number=unit_number,
        page=page,
        per_page=per_page,
    )


# ВРЕМЕННО: endpoint без авторизации для теста
@router.get("/public")
def list_residents_public(
    db: Session = Depends(get_db),
    block_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    rtype: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    unit_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации.
    """
    return _list_residents_internal(
        db=db,
        block_id=block_id,
        status=status,
        rtype=rtype,
        q=q,
        unit_number=unit_number,
        page=page,
        per_page=per_page,
    )


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

    # Начальный долг: создаём отдельный инвойс "opening balance",
    # чтобы он учитывался во всех расчётах долга (через суммы счетов).
    opening_debt = payload.debt or 0.0
    if opening_debt:
        try:
            opening_debt_dec = Decimal(str(opening_debt))
        except (InvalidOperation, Exception):
            raise HTTPException(status_code=400, detail="Invalid debt value")
        if opening_debt_dec < 0:
            raise HTTPException(status_code=400, detail="Debt cannot be negative")
        if opening_debt_dec > 0:
            # Подбираем период, чтобы не конфликтовать с uq_invoice_resident_period
            y, m = 1900, 1
            while True:
                exists_id = db.execute(
                    select(Invoice.id).where(
                        Invoice.resident_id == resident.id,
                        Invoice.period_year == y,
                        Invoice.period_month == m,
                    )
                ).scalar_one_or_none()
                if not exists_id:
                    break
                m += 1
                if m > 12:
                    y += 1
                    m = 1

            inv = Invoice(
                resident_id=resident.id,
                number=f"OPEN/{resident.id:06d}",
                status=InvoiceStatus.ISSUED,
                due_date=None,
                notes="Начальный долг (до внедрения системы)",
                period_year=y,
                period_month=m,
                amount_net=opening_debt_dec,
                amount_vat=Decimal("0"),
                amount_total=opening_debt_dec,
                created_by_id=actor.id,
            )
            db.add(inv)
            db.flush()

            db.add(InvoiceLine(
                invoice_id=inv.id,
                meter_reading_id=None,
                description="Начальный долг",
                amount_net=opening_debt_dec,
                amount_vat=Decimal("0"),
                amount_total=opening_debt_dec,
            ))
    
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
    
    opening_debt = _get_opening_debt(db, resident.id)

    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "debt": float(opening_debt),
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

    # Начальный долг (public endpoint): создаём "opening invoice"
    opening_debt = payload.debt or 0.0
    if opening_debt:
        try:
            opening_debt_dec = Decimal(str(opening_debt))
        except (InvalidOperation, Exception):
            raise HTTPException(status_code=400, detail="Invalid debt value")
        if opening_debt_dec < 0:
            raise HTTPException(status_code=400, detail="Debt cannot be negative")
        if opening_debt_dec > 0:
            y, m = 1900, 1
            while True:
                exists_id = db.execute(
                    select(Invoice.id).where(
                        Invoice.resident_id == resident.id,
                        Invoice.period_year == y,
                        Invoice.period_month == m,
                    )
                ).scalar_one_or_none()
                if not exists_id:
                    break
                m += 1
                if m > 12:
                    y += 1
                    m = 1

            inv = Invoice(
                resident_id=resident.id,
                number=f"OPEN/{resident.id:06d}",
                status=InvoiceStatus.ISSUED,
                due_date=None,
                notes="Начальный долг (до внедрения системы)",
                period_year=y,
                period_month=m,
                amount_net=opening_debt_dec,
                amount_vat=Decimal("0"),
                amount_total=opening_debt_dec,
                created_by_id=None,
            )
            db.add(inv)
            db.flush()

            db.add(InvoiceLine(
                invoice_id=inv.id,
                meter_reading_id=None,
                description="Начальный долг",
                amount_net=opening_debt_dec,
                amount_vat=Decimal("0"),
                amount_total=opening_debt_dec,
            ))
    
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
    opening_debt = _get_opening_debt(db, resident.id)

    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "debt": float(opening_debt),
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

    opening_debt = _get_opening_debt(db, resident.id)

    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "debt": float(opening_debt),
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

    opening_debt = _get_opening_debt(db, resident.id)

    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "debt": float(opening_debt),
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

    # ---- Начальный долг (opening invoice) ----
    if payload.debt is not None:
        try:
            new_debt = Decimal(str(payload.debt or 0))
        except (InvalidOperation, Exception):
            raise HTTPException(status_code=400, detail="Invalid debt value")
        if new_debt < 0:
            raise HTTPException(status_code=400, detail="Debt cannot be negative")

        opening_inv = _get_opening_invoice(db, resident.id)

        if opening_inv is None:
            # Если долга нет/0 — ничего не создаём
            if new_debt > 0:
                # Подбираем период, чтобы не конфликтовать с uq_invoice_resident_period
                y, m = 1900, 1
                while True:
                    exists_id = db.execute(
                        select(Invoice.id).where(
                            Invoice.resident_id == resident.id,
                            Invoice.period_year == y,
                            Invoice.period_month == m,
                        )
                    ).scalar_one_or_none()
                    if not exists_id:
                        break
                    m += 1
                    if m > 12:
                        y += 1
                        m = 1

                opening_inv = Invoice(
                    resident_id=resident.id,
                    number=_opening_invoice_number(resident.id),
                    status=InvoiceStatus.ISSUED,
                    due_date=None,
                    notes="Начальный долг (до внедрения системы)",
                    period_year=y,
                    period_month=m,
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                    created_by_id=actor.id,
                )
                db.add(opening_inv)
                db.flush()
                db.add(InvoiceLine(
                    invoice_id=opening_inv.id,
                    meter_reading_id=None,
                    description="Начальный долг",
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                ))
        else:
            applied = (
                db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
                .filter(PaymentApplication.invoice_id == opening_inv.id)
                .scalar()
                or 0
            )
            applied_dec = Decimal(str(applied))
            if new_debt < applied_dec:
                raise HTTPException(status_code=400, detail="Debt cannot be less than already paid amount")

            # Если ставим 0 и ничего не оплачено — отменяем инвойс, чтобы он не участвовал в расчёте долга
            if new_debt == 0 and applied_dec == 0:
                opening_inv.status = InvoiceStatus.CANCELED
                opening_inv.amount_net = Decimal("0")
                opening_inv.amount_vat = Decimal("0")
                opening_inv.amount_total = Decimal("0")
            else:
                opening_inv.status = (
                    InvoiceStatus.PAID if (new_debt == applied_dec and new_debt > 0)
                    else (InvoiceStatus.ISSUED if applied_dec == 0 else InvoiceStatus.PARTIAL)
                )
                opening_inv.notes = "Начальный долг (до внедрения системы)"
                opening_inv.amount_net = new_debt
                opening_inv.amount_vat = Decimal("0")
                opening_inv.amount_total = new_debt

            # Синхронизируем строки (если их несколько — делаем одинаковыми)
            lines = db.execute(
                select(InvoiceLine).where(InvoiceLine.invoice_id == opening_inv.id)
            ).scalars().all()
            if not lines:
                db.add(InvoiceLine(
                    invoice_id=opening_inv.id,
                    meter_reading_id=None,
                    description="Начальный долг",
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                ))
            else:
                for ln in lines:
                    ln.amount_net = new_debt
                    ln.amount_vat = Decimal("0")
                    ln.amount_total = new_debt
    
    # Обновление/синхронизация счётчиков (БЕЗ физического удаления тех, у кого есть показания)
    # Это предотвращает "пропадание показаний" из-за FK resident_meter_id ON DELETE CASCADE.
    if payload.meters is not None:
        try:
            incoming = _parse_meters(payload.meters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        existing_meters: list[ResidentMeter] = (
            db.query(ResidentMeter)
            .filter(ResidentMeter.resident_id == resident.id)
            .all()
        )
        existing_by_id = {m.id: m for m in existing_meters}

        if existing_by_id:
            meters_with_readings = {
                mid for (mid,) in db.query(MeterReading.resident_meter_id)
                .filter(MeterReading.resident_meter_id.in_(list(existing_by_id.keys())))
                .distinct()
                .all()
            }
        else:
            meters_with_readings = set()

        seen_existing_ids: set[int] = set()

        def validate_tariff(tariff_id: int, meter_type_enum: MeterType, existing_meter: ResidentMeter | None):
            tariff = db.get(Tariff, tariff_id)
            if not tariff:
                raise HTTPException(status_code=404, detail=f"Tariff {tariff_id} not found")
            if tariff.meter_type != meter_type_enum:
                raise HTTPException(status_code=400, detail=f"Tariff {tariff_id} meter_type mismatch")
            # Не даём назначать неактивные тарифы на новые/изменённые счётчики.
            # Но разрешаем сохранить старую привязку (если она уже была).
            if not tariff.is_active:
                if not (existing_meter and existing_meter.tariff_id == tariff_id):
                    raise HTTPException(status_code=400, detail=f"Tariff {tariff_id} is inactive")
            return tariff

        # 1) Upsert incoming meters
        for m_data in incoming:
            meter_id = m_data.get("id")
            meter_type = m_data["meter_type"]
            serial = m_data["serial"]
            initial_reading = m_data["initial_reading"]
            tariff_id = m_data["tariff_id"]

            existing_meter: ResidentMeter | None = None
            if meter_id is not None:
                existing_meter = existing_by_id.get(int(meter_id))
                if not existing_meter or existing_meter.resident_id != resident.id:
                    raise HTTPException(status_code=400, detail=f"Meter {meter_id} not found for this resident")
            else:
                # Best-effort match for backwards compatibility (older SPA payload without meter id)
                # Prefer active meters first to avoid accidentally reactivating historical ones.
                candidates = [
                    em for em in existing_meters
                    if em.meter_type == meter_type
                    and (em.serial_number or "") == (serial or "")
                    and em.tariff_id == tariff_id
                ]
                candidates = sorted(candidates, key=lambda x: (not x.is_active, x.id))
                existing_meter = candidates[0] if candidates else None

            validate_tariff(tariff_id, meter_type, existing_meter)

            if existing_meter:
                # Обновляем существующий счётчик
                existing_meter.is_active = True
                existing_meter.serial_number = serial
                existing_meter.tariff_id = tariff_id

                # Не меняем initial_reading, если есть показания — иначе можем сломать базовую логику "опорного"
                if existing_meter.id not in meters_with_readings:
                    existing_meter.initial_reading = initial_reading
                seen_existing_ids.add(existing_meter.id)
            else:
                # Создаём новый счётчик
                db.add(ResidentMeter(
                    resident_id=resident.id,
                    meter_type=meter_type,
                    serial_number=serial,
                    initial_reading=initial_reading,
                    tariff_id=tariff_id,
                    is_active=True,
                ))

        # 2) Deactivate (or delete) meters that are missing in incoming payload
        for em in existing_meters:
            if em.id in seen_existing_ids:
                continue
            if em.id in meters_with_readings:
                em.is_active = False
            else:
                db.delete(em)
    
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
    opening_debt = _get_opening_debt(db, resident.id)

    return {
        "id": resident.id,
        "block_id": resident.block_id,
        "block_name": resident.block.name if resident.block else None,
        "unit_number": resident.unit_number,
        "resident_type": resident.resident_type.value,
        "customer_type": resident.customer_type.value,
        "status": resident.status.value,
        "debt": float(opening_debt),
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

    # ---- Начальный долг (opening invoice) ----
    if payload.debt is not None:
        try:
            new_debt = Decimal(str(payload.debt or 0))
        except (InvalidOperation, Exception):
            raise HTTPException(status_code=400, detail="Invalid debt value")
        if new_debt < 0:
            raise HTTPException(status_code=400, detail="Debt cannot be negative")

        opening_inv = _get_opening_invoice(db, resident.id)

        if opening_inv is None:
            if new_debt > 0:
                y, m = 1900, 1
                while True:
                    exists_id = db.execute(
                        select(Invoice.id).where(
                            Invoice.resident_id == resident.id,
                            Invoice.period_year == y,
                            Invoice.period_month == m,
                        )
                    ).scalar_one_or_none()
                    if not exists_id:
                        break
                    m += 1
                    if m > 12:
                        y += 1
                        m = 1

                opening_inv = Invoice(
                    resident_id=resident.id,
                    number=_opening_invoice_number(resident.id),
                    status=InvoiceStatus.ISSUED,
                    due_date=None,
                    notes="Начальный долг (до внедрения системы)",
                    period_year=y,
                    period_month=m,
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                    created_by_id=None,
                )
                db.add(opening_inv)
                db.flush()
                db.add(InvoiceLine(
                    invoice_id=opening_inv.id,
                    meter_reading_id=None,
                    description="Начальный долг",
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                ))
        else:
            applied = (
                db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
                .filter(PaymentApplication.invoice_id == opening_inv.id)
                .scalar()
                or 0
            )
            applied_dec = Decimal(str(applied))
            if new_debt < applied_dec:
                raise HTTPException(status_code=400, detail="Debt cannot be less than already paid amount")

            if new_debt == 0 and applied_dec == 0:
                opening_inv.status = InvoiceStatus.CANCELED
                opening_inv.amount_net = Decimal("0")
                opening_inv.amount_vat = Decimal("0")
                opening_inv.amount_total = Decimal("0")
            else:
                opening_inv.status = (
                    InvoiceStatus.PAID if (new_debt == applied_dec and new_debt > 0)
                    else (InvoiceStatus.ISSUED if applied_dec == 0 else InvoiceStatus.PARTIAL)
                )
                opening_inv.notes = "Начальный долг (до внедрения системы)"
                opening_inv.amount_net = new_debt
                opening_inv.amount_vat = Decimal("0")
                opening_inv.amount_total = new_debt

            lines = db.execute(
                select(InvoiceLine).where(InvoiceLine.invoice_id == opening_inv.id)
            ).scalars().all()
            if not lines:
                db.add(InvoiceLine(
                    invoice_id=opening_inv.id,
                    meter_reading_id=None,
                    description="Начальный долг",
                    amount_net=new_debt,
                    amount_vat=Decimal("0"),
                    amount_total=new_debt,
                ))
            else:
                for ln in lines:
                    ln.amount_net = new_debt
                    ln.amount_vat = Decimal("0")
                    ln.amount_total = new_debt
    
    # Обновление/синхронизация счётчиков (БЕЗ физического удаления тех, у кого есть показания)
    if payload.meters is not None:
        try:
            incoming = _parse_meters(payload.meters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        existing_meters: list[ResidentMeter] = (
            db.query(ResidentMeter)
            .filter(ResidentMeter.resident_id == resident.id)
            .all()
        )
        existing_by_id = {m.id: m for m in existing_meters}

        if existing_by_id:
            meters_with_readings = {
                mid for (mid,) in db.query(MeterReading.resident_meter_id)
                .filter(MeterReading.resident_meter_id.in_(list(existing_by_id.keys())))
                .distinct()
                .all()
            }
        else:
            meters_with_readings = set()

        seen_existing_ids: set[int] = set()

        def validate_tariff(tariff_id: int, meter_type_enum: MeterType, existing_meter: ResidentMeter | None):
            tariff = db.get(Tariff, tariff_id)
            if not tariff:
                raise HTTPException(status_code=404, detail=f"Tariff {tariff_id} not found")
            if tariff.meter_type != meter_type_enum:
                raise HTTPException(status_code=400, detail=f"Tariff {tariff_id} meter_type mismatch")
            if not tariff.is_active:
                if not (existing_meter and existing_meter.tariff_id == tariff_id):
                    raise HTTPException(status_code=400, detail=f"Tariff {tariff_id} is inactive")
            return tariff

        for m_data in incoming:
            meter_id = m_data.get("id")
            meter_type = m_data["meter_type"]
            serial = m_data["serial"]
            initial_reading = m_data["initial_reading"]
            tariff_id = m_data["tariff_id"]

            existing_meter: ResidentMeter | None = None
            if meter_id is not None:
                existing_meter = existing_by_id.get(int(meter_id))
                if not existing_meter or existing_meter.resident_id != resident.id:
                    raise HTTPException(status_code=400, detail=f"Meter {meter_id} not found for this resident")
            else:
                candidates = [
                    em for em in existing_meters
                    if em.meter_type == meter_type
                    and (em.serial_number or "") == (serial or "")
                    and em.tariff_id == tariff_id
                ]
                candidates = sorted(candidates, key=lambda x: (not x.is_active, x.id))
                existing_meter = candidates[0] if candidates else None

            validate_tariff(tariff_id, meter_type, existing_meter)

            if existing_meter:
                existing_meter.is_active = True
                existing_meter.serial_number = serial
                existing_meter.tariff_id = tariff_id
                if existing_meter.id not in meters_with_readings:
                    existing_meter.initial_reading = initial_reading
                seen_existing_ids.add(existing_meter.id)
            else:
                db.add(ResidentMeter(
                    resident_id=resident.id,
                    meter_type=meter_type,
                    serial_number=serial,
                    initial_reading=initial_reading,
                    tariff_id=tariff_id,
                    is_active=True,
                ))

        for em in existing_meters:
            if em.id in seen_existing_ids:
                continue
            if em.id in meters_with_readings:
                em.is_active = False
            else:
                db.delete(em)
    
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

