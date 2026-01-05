from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import (
    User, RoleEnum,
    Notification, NotificationStatus,
    Resident, Block
)
from ..deps import get_current_user


router = APIRouter(prefix="/api/notifications", tags=["notifications-api"])


# Pydantic models
class NotificationOut(BaseModel):
    id: int
    user_id: int
    resident_id: Optional[int] = None
    message: str
    status: str  # "UNREAD" or "READ"
    created_at: datetime
    read_at: Optional[datetime] = None
    
    # Новые поля
    notification_type: Optional[str] = None  # INVOICE, NEWS, APPEAL
    related_id: Optional[int] = None  # ID счета, новости и т.д.
    
    # User info
    user_full_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    
    # Resident info
    resident_code: Optional[str] = None  # "A / 205"
    resident_info: Optional[str] = None  # "Блок A, №205"
    block_name: Optional[str] = None
    unit_number: Optional[str] = None

    class Config:
        from_attributes = True


def _list_notifications_internal(
    db: Session,
    status_filter: Optional[str] = None,
    resident_id: Optional[int] = None,
    block_id: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
):
    """Внутренняя функция для получения списка уведомлений."""
    from sqlalchemy import or_
    # В админ-панели показываем только обращения (APPEAL), 
    # исключая счета (INVOICE) и новости (NEWS).
    query = db.query(Notification).join(User, User.id == Notification.user_id).filter(
        or_(
            Notification.notification_type == "APPEAL",
            Notification.notification_type == None
        )
    )
    
    # Join с Resident для фильтрации
    if resident_id or block_id or q:
        query = query.outerjoin(Resident, Resident.id == Notification.resident_id)
        if block_id:
            query = query.outerjoin(Block, Block.id == Resident.block_id)
    
    # Фильтр по статусу
    if status_filter and status_filter.upper() in {s.value for s in NotificationStatus}:
        status_enum = NotificationStatus(status_filter.upper())
        query = query.filter(Notification.status == status_enum)
    
    # Фильтр по резиденту
    if resident_id:
        query = query.filter(Notification.resident_id == resident_id)
    
    # Фильтр по блоку
    if block_id:
        query = query.filter(Block.name == block_id)
    
    # Поиск
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Notification.message.ilike(like),
                User.full_name.ilike(like),
                User.phone.ilike(like),
                User.email.ilike(like),
            )
        )
    
    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, last_page))
    
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Преобразуем в формат для ответа
    result = []
    for notif in notifications:
        resident_code = None
        resident_info = None
        block_name = None
        unit_number = None
        
        if notif.resident:
            block_name = notif.resident.block.name if notif.resident.block else None
            unit_number = notif.resident.unit_number
            if block_name and unit_number:
                resident_code = f"{block_name} / {unit_number}"
                resident_info = f"Блок {block_name}, №{unit_number}"
        
        result.append(NotificationOut(
            id=notif.id,
            user_id=notif.user_id,
            resident_id=notif.resident_id,
            message=notif.message,
            status=notif.status.value,
            created_at=notif.created_at,
            read_at=notif.read_at,
            notification_type=notif.notification_type,
            related_id=notif.related_id,
            user_full_name=notif.user.full_name,
            user_phone=notif.user.phone,
            user_email=notif.user.email,
            resident_code=resident_code,
            resident_info=resident_info,
            block_name=block_name,
            unit_number=unit_number,
        ))
    
    return {
        "notifications": result,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
        }
    }


def _get_notification_internal(
    db: Session,
    notification_id: int,
):
    """Внутренняя функция для получения одного уведомления."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return None
    
    # Помечаем как прочитанное, если еще не прочитано
    if notif.status == NotificationStatus.UNREAD:
        notif.status = NotificationStatus.READ
        notif.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notif)
    
    resident_code = None
    resident_info = None
    block_name = None
    unit_number = None
    
    if notif.resident:
        block_name = notif.resident.block.name if notif.resident.block else None
        unit_number = notif.resident.unit_number
        if block_name and unit_number:
            resident_code = f"{block_name} / {unit_number}"
            resident_info = f"Блок {block_name}, №{unit_number}"
    
    return NotificationOut(
        id=notif.id,
        user_id=notif.user_id,
        resident_id=notif.resident_id,
        message=notif.message,
        status=notif.status.value,
        created_at=notif.created_at,
        read_at=notif.read_at,
        notification_type=notif.notification_type,
        related_id=notif.related_id,
        user_full_name=notif.user.full_name,
        user_phone=notif.user.phone,
        user_email=notif.user.email,
        resident_code=resident_code,
        resident_info=resident_info,
        block_name=block_name,
        unit_number=unit_number,
    )


@router.get("/")
def list_notifications(
    status: Optional[str] = Query(None, alias="status"),
    resident_id: Optional[int] = Query(None),
    block: Optional[str] = Query(None, alias="block"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список уведомлений (требует авторизации)."""
    try:
        return _list_notifications_internal(
            db=db,
            status_filter=status,
            resident_id=resident_id,
            block_id=block,
            q=q,
            page=page,
            per_page=per_page,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public")
def list_notifications_public(
    status: Optional[str] = Query(None, alias="status"),
    resident_id: Optional[int] = Query(None),
    block: Optional[str] = Query(None, alias="block"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Получить список уведомлений (публичный endpoint без авторизации)."""
    try:
        return _list_notifications_internal(
            db=db,
            status_filter=status,
            resident_id=resident_id,
            block_id=block,
            q=q,
            page=page,
            per_page=per_page,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
def get_unread_count_public(db: Session = Depends(get_db)):
    """Получить количество непрочитанных уведомлений (публичный endpoint)."""
    from sqlalchemy import func, or_
    # Считаем только обращения (APPEAL), так как в админке нужны только они.
    # Счета (INVOICE) и новости (NEWS) — только для жителей.
    count = db.query(func.count(Notification.id)).filter(
        Notification.status == NotificationStatus.UNREAD,
        or_(
            Notification.notification_type == "APPEAL",
            Notification.notification_type == None
        )
    ).scalar()
    return {"count": count or 0}


@router.get("/user/me")
def get_user_notifications(
    status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить уведомления текущего пользователя (для резидентской панели)."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    # Фильтр по статусу
    if status and status.upper() in {s.value for s in NotificationStatus}:
        status_enum = NotificationStatus(status.upper())
        query = query.filter(Notification.status == status_enum)
    
    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, last_page))
    
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    result = []
    for notif in notifications:
        resident_code = None
        resident_info = None
        block_name = None
        unit_number = None
        
        if notif.resident:
            block_name = notif.resident.block.name if notif.resident.block else None
            unit_number = notif.resident.unit_number
            if block_name and unit_number:
                resident_code = f"{block_name} / {unit_number}"
                resident_info = f"Блок {block_name}, №{unit_number}"
        
        result.append(NotificationOut(
            id=notif.id,
            user_id=notif.user_id,
            resident_id=notif.resident_id,
            message=notif.message,
            status=notif.status.value,
            created_at=notif.created_at,
            read_at=notif.read_at,
            notification_type=notif.notification_type,
            related_id=notif.related_id,
            user_full_name=notif.user.full_name,
            user_phone=notif.user.phone,
            user_email=notif.user.email,
            resident_code=resident_code,
            resident_info=resident_info,
            block_name=block_name,
            unit_number=unit_number,
        ))
    
    return {
        "notifications": result,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
        }
    }


@router.get("/user/me/unread-count")
def get_user_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить количество непрочитанных уведомлений текущего пользователя."""
    from sqlalchemy import func
    count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.status == NotificationStatus.UNREAD
    ).scalar()
    return {"count": count or 0}


@router.get("/{notification_id}")
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить одно уведомление по ID (требует авторизации)."""
    notif = _get_notification_internal(db, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.get("/{notification_id}/public")
def get_notification_public(
    notification_id: int,
    db: Session = Depends(get_db),
):
    """Получить одно уведомление по ID (публичный endpoint без авторизации)."""
    notif = _get_notification_internal(db, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить уведомление (требует авторизации)."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notif)
    db.commit()
    
    return {"ok": True, "message": "Notification deleted"}


@router.delete("/{notification_id}/public")
def delete_notification_public(
    notification_id: int,
    db: Session = Depends(get_db),
):
    """Удалить уведомление (публичный endpoint без авторизации)."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notif)
    db.commit()
    
    return {"ok": True, "message": "Notification deleted"}

