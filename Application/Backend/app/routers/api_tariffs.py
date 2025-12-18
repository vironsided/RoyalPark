from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import json

from ..database import get_db
from ..models import Tariff, TariffStep, MeterType, CustomerType
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/api/tariffs", tags=["tariffs-api"])


class TariffStepOut(BaseModel):
    id: int
    from_value: Optional[float] = None
    to_value: Optional[float] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    price: float

    class Config:
        from_attributes = True


class TariffStepCreate(BaseModel):
    from_value: Optional[float] = None
    to_value: Optional[float] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    price: float


class TariffOut(BaseModel):
    id: int
    name: str
    meter_type: str
    customer_type: str
    vat_percent: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    steps: List[TariffStepOut] = []

    class Config:
        from_attributes = True


class TariffCreate(BaseModel):
    name: str
    meter_type: str
    customer_type: str
    vat_percent: int
    steps: List[TariffStepCreate]


class TariffUpdate(BaseModel):
    name: Optional[str] = None
    meter_type: Optional[str] = None
    customer_type: Optional[str] = None
    vat_percent: Optional[int] = None
    is_active: Optional[bool] = None
    steps: Optional[List[TariffStepCreate]] = None


def _to_decimal(value: object) -> Decimal:
    """Безопасно приводит вход к Decimal."""
    return Decimal(str(value))


def _parse_steps(steps_data: List[TariffStepCreate], meter_type: str) -> List[tuple]:
    """Валидация и преобразование ступеней."""
    if not steps_data:
        raise ValueError("empty_steps")
    
    is_construction = meter_type == MeterType.CONSTRUCTION.value
    steps = []
    
    for i, step in enumerate(steps_data):
        if is_construction:
            if not step.from_date or not step.to_date:
                raise ValueError(f"invalid_dates_{i}")
            if step.to_date < step.from_date:
                raise ValueError(f"date_order_{i}")
            if step.price < 0:
                raise ValueError(f"negative_values_{i}")
            steps.append((step.from_date, step.to_date, _to_decimal(step.price)))
        else:
            f = _to_decimal(step.from_value or 0)
            t = None if step.to_value is None else _to_decimal(step.to_value)
            p = _to_decimal(step.price)
            
            if f < 0 or p < 0:
                raise ValueError(f"negative_values_{i}")
            if t is not None and t <= f:
                raise ValueError(f"range_order_{i}")
            
            steps.append((f, t, p))
    
    # Проверка непрерывности (для не-construction)
    if not is_construction:
        for i in range(len(steps) - 1):
            f1, t1, _ = steps[i]
            f2, _t2, _ = steps[i + 1]
            if t1 is None:
                raise ValueError("infinite_not_last")
            if f2 != t1:
                raise ValueError("not_continuous")
    
    return steps


# ВРЕМЕННО: endpoint без авторизации для теста (должен быть ПЕРЕД динамическими маршрутами!)
@router.get("/public", response_model=List[TariffOut])
@router.get("/public/", response_model=List[TariffOut])
def list_tariffs_public(
    db: Session = Depends(get_db),
    meter: Optional[str] = None,
    ctype: Optional[str] = None,
    q: Optional[str] = None,
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста SPA."""
    query = db.execute(select(Tariff)).scalars().all()
    
    if meter and meter in {m.value for m in MeterType}:
        query = [t for t in query if t.meter_type == MeterType(meter)]
    
    if ctype and ctype in {c.value for c in CustomerType}:
        query = [t for t in query if t.customer_type == CustomerType(ctype)]
    
    if q:
        needle = q.strip().lower()
        query = [t for t in query if needle in t.name.lower()]
    
    tariffs = sorted(query, key=lambda t: t.id)
    return tariffs


@router.get("/{tariff_id}/public", response_model=TariffOut)
def get_tariff_public(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    return tariff


@router.get("", response_model=List[TariffOut])
@router.get("/", response_model=List[TariffOut])
def list_tariffs_api(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    meter: Optional[str] = None,
    ctype: Optional[str] = None,
    q: Optional[str] = None,
):
    """
    JSON-список тарифов для SPA-админки с фильтрами.
    """
    query = db.execute(select(Tariff)).scalars().all()
    
    if meter and meter in {m.value for m in MeterType}:
        query = [t for t in query if t.meter_type == MeterType(meter)]
    
    if ctype and ctype in {c.value for c in CustomerType}:
        query = [t for t in query if t.customer_type == CustomerType(ctype)]
    
    if q:
        needle = q.strip().lower()
        query = [t for t in query if needle in t.name.lower()]
    
    tariffs = sorted(query, key=lambda t: t.id)
    return tariffs


@router.get("/{tariff_id}", response_model=TariffOut)
def get_tariff_api(
    tariff_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """Получение одного тарифа по ID."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    return tariff


# ВРЕМЕННО: endpoint без авторизации для создания (должен быть ПЕРЕД обычным!)
@router.post("/public", response_model=TariffOut, status_code=status.HTTP_201_CREATED)
def create_tariff_public(
    payload: TariffCreate,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста SPA."""
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Название не может быть пустым")
    
    if payload.meter_type not in {m.value for m in MeterType}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип счётчика")
    
    if payload.customer_type not in {c.value for c in CustomerType}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип клиента")
    
    if not (0 <= payload.vat_percent <= 100):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="НДС должен быть от 0 до 100")
    
    exists = db.execute(
        select(Tariff.id).where(
            func.lower(Tariff.name) == func.lower(name),
            Tariff.meter_type == MeterType(payload.meter_type),
            Tariff.customer_type == CustomerType(payload.customer_type),
        )
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тариф с таким названием уже существует")
    
    try:
        steps = _parse_steps(payload.steps, payload.meter_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка валидации ступеней: {e}")
    
    try:
        tariff = Tariff(
            name=name,
            meter_type=MeterType(payload.meter_type),
            customer_type=CustomerType(payload.customer_type),
            vat_percent=payload.vat_percent,
            created_by_id=None,
        )
        db.add(tariff)
        db.flush()
        
        is_construction = payload.meter_type == MeterType.CONSTRUCTION.value
        if is_construction:
            for start, end, price in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_date=start,
                    to_date=end,
                    price=price,
                ))
        else:
            for f, t, p in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_value=float(f),
                    to_value=float(t) if t is not None else None,
                    price=float(p),
                ))
        
        db.commit()
        db.refresh(tariff)
        return tariff
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания тарифа: {str(e)}")


@router.post("", response_model=TariffOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TariffOut, status_code=status.HTTP_201_CREATED)
def create_tariff_api(
    payload: TariffCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """Создание тарифа из SPA."""
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Название не может быть пустым")
    
    if payload.meter_type not in {m.value for m in MeterType}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип счётчика")
    
    if payload.customer_type not in {c.value for c in CustomerType}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный тип клиента")
    
    if not (0 <= payload.vat_percent <= 100):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="НДС должен быть от 0 до 100")
    
    # Проверка уникальности
    exists = db.execute(
        select(Tariff.id).where(
            func.lower(Tariff.name) == func.lower(name),
            Tariff.meter_type == MeterType(payload.meter_type),
            Tariff.customer_type == CustomerType(payload.customer_type),
        )
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тариф с таким названием уже существует")
    
    try:
        steps = _parse_steps(payload.steps, payload.meter_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка валидации ступеней: {e}")
    
    try:
        tariff = Tariff(
            name=name,
            meter_type=MeterType(payload.meter_type),
            customer_type=CustomerType(payload.customer_type),
            vat_percent=payload.vat_percent,
            created_by_id=actor.id,
        )
        db.add(tariff)
        db.flush()
        
        is_construction = payload.meter_type == MeterType.CONSTRUCTION.value
        if is_construction:
            for start, end, price in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_date=start,
                    to_date=end,
                    price=price,
                ))
        else:
            for f, t, p in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_value=float(f),
                    to_value=float(t) if t is not None else None,
                    price=float(p),
                ))
        
        db.commit()
        db.refresh(tariff)
        return tariff
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка создания тарифа: {str(e)}")




@router.put("/{tariff_id}", response_model=TariffOut)
def update_tariff_api(
    tariff_id: int,
    payload: TariffUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """Обновление тарифа."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    
    meter_type = payload.meter_type or tariff.meter_type.value
    
    if payload.name is not None:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Название не может быть пустым")
        
        exists = db.execute(
            select(Tariff.id).where(
                Tariff.id != tariff_id,
                func.lower(Tariff.name) == func.lower(name),
                Tariff.meter_type == MeterType(meter_type),
                Tariff.customer_type == CustomerType(payload.customer_type or tariff.customer_type.value),
            )
        ).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тариф с таким названием уже существует")
        
        tariff.name = name
    
    if payload.meter_type is not None:
        tariff.meter_type = MeterType(payload.meter_type)
    
    if payload.customer_type is not None:
        tariff.customer_type = CustomerType(payload.customer_type)
    
    if payload.vat_percent is not None:
        if not (0 <= payload.vat_percent <= 100):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="НДС должен быть от 0 до 100")
        tariff.vat_percent = payload.vat_percent
    
    if payload.is_active is not None:
        tariff.is_active = payload.is_active
    
    if payload.steps is not None:
        try:
            steps = _parse_steps(payload.steps, meter_type)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка валидации ступеней: {e}")
        
        # Удаляем старые ступени
        db.query(TariffStep).filter(TariffStep.tariff_id == tariff_id).delete()
        
        # Добавляем новые
        is_construction = meter_type == MeterType.CONSTRUCTION.value
        if is_construction:
            for start, end, price in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_date=start,
                    to_date=end,
                    price=price,
                ))
        else:
            for f, t, p in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_value=float(f),
                    to_value=float(t) if t is not None else None,
                    price=float(p),
                ))
    
    db.commit()
    db.refresh(tariff)
    return tariff


# ВРЕМЕННО: публичный endpoint для обновления
@router.put("/{tariff_id}/public", response_model=TariffOut)
def update_tariff_public(
    tariff_id: int,
    payload: TariffUpdate,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    
    meter_type = payload.meter_type or tariff.meter_type.value
    
    if payload.name is not None:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Название не может быть пустым")
        
        exists = db.execute(
            select(Tariff.id).where(
                Tariff.id != tariff_id,
                func.lower(Tariff.name) == func.lower(name),
                Tariff.meter_type == MeterType(meter_type),
                Tariff.customer_type == CustomerType(payload.customer_type or tariff.customer_type.value),
            )
        ).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тариф с таким названием уже существует")
        
        tariff.name = name
    
    if payload.meter_type is not None:
        tariff.meter_type = MeterType(payload.meter_type)
    
    if payload.customer_type is not None:
        tariff.customer_type = CustomerType(payload.customer_type)
    
    if payload.vat_percent is not None:
        if not (0 <= payload.vat_percent <= 100):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="НДС должен быть от 0 до 100")
        tariff.vat_percent = payload.vat_percent
    
    if payload.is_active is not None:
        tariff.is_active = payload.is_active
    
    if payload.steps is not None:
        try:
            steps = _parse_steps(payload.steps, meter_type)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка валидации ступеней: {e}")
        
        db.query(TariffStep).filter(TariffStep.tariff_id == tariff_id).delete()
        
        is_construction = meter_type == MeterType.CONSTRUCTION.value
        if is_construction:
            for start, end, price in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_date=start,
                    to_date=end,
                    price=price,
                ))
        else:
            for f, t, p in steps:
                db.add(TariffStep(
                    tariff_id=tariff.id,
                    from_value=float(f),
                    to_value=float(t) if t is not None else None,
                    price=float(p),
                ))
    
    db.commit()
    db.refresh(tariff)
    return tariff


@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tariff_api(
    tariff_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """Удаление тарифа."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    
    db.delete(tariff)
    db.commit()
    return None


# ВРЕМЕННО: публичный endpoint для удаления
@router.delete("/{tariff_id}/public", status_code=status.HTTP_204_NO_CONTENT)
def delete_tariff_public(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    tariff = db.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")
    
    db.delete(tariff)
    db.commit()
    return None

