from __future__ import annotations
from typing import List, Optional

from datetime import datetime

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from starlette import status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import Notification, NotificationStatus, RoleEnum, User, Resident, Block

router = APIRouter(prefix="/notifications", tags=["notifications"])
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def notifications_page(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: str = "all",
):
    query = db.query(Notification).order_by(Notification.created_at.desc())
    status_filter = (status_filter or "all").upper()
    if status_filter == NotificationStatus.UNREAD.value:
        query = query.filter(Notification.status == NotificationStatus.UNREAD)
    elif status_filter == NotificationStatus.READ.value:
        query = query.filter(Notification.status == NotificationStatus.READ)

    notifications = query.all()

    return templates.TemplateResponse(
        "notifications.html",
        {
            "request": request,
            "user": user,
            "notifications": notifications,
            "status_filter": status_filter,
            "NotificationStatus": NotificationStatus,
        },
    )


# Публичный JSON endpoint для получения одного уведомления (должен быть перед маршрутом с авторизацией)
@router.get("/{notification_id}/json", response_model=dict)
def get_notification_json_public(
    notification_id: int,
    db: Session = Depends(get_db),
):
    """JSON endpoint для получения одного уведомления (публичный, без авторизации)."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return JSONResponse({"error": "Notification not found"}, status_code=404)
    
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
    
    return {
        "id": notif.id,
        "user_id": notif.user_id,
        "resident_id": notif.resident_id,
        "message": notif.message,
        "status": notif.status.value,
        "created_at": notif.created_at.isoformat(),
        "read_at": notif.read_at.isoformat() if notif.read_at else None,
        "user_full_name": notif.user.full_name,
        "user_phone": notif.user.phone,
        "user_email": notif.user.email,
        "resident_code": resident_code,
        "resident_info": resident_info,
        "block_name": block_name,
        "unit_number": unit_number,
    }


@router.post(
    "/{notification_id}/delete",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def notification_delete(
    notification_id: int,
    db: Session = Depends(get_db),
    status_filter: str = "all",
):
    notif = db.get(Notification, notification_id)
    if not notif:
        return RedirectResponse(
            url=f"/notifications?status_filter={status_filter}&error=notfound",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    db.delete(notif)
    db.commit()

    return RedirectResponse(
        url=f"/notifications?status_filter={status_filter}&ok=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# JSON API endpoints для frontend
class NotificationOut(BaseModel):
    id: int
    user_id: int
    resident_id: Optional[int] = None
    message: str
    status: str
    created_at: str
    read_at: Optional[str] = None
    user_full_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    resident_code: Optional[str] = None
    resident_info: Optional[str] = None
    block_name: Optional[str] = None
    unit_number: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/json", response_model=dict)
def list_notifications_json(
    status: Optional[str] = Query(None, alias="status"),
    resident_id: Optional[int] = Query(None),
    block: Optional[str] = Query(None, alias="block"),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """JSON endpoint для получения списка уведомлений (публичный, без авторизации)."""
    try:
        query = db.query(Notification).join(User, User.id == Notification.user_id)
        
        # Join с Resident для фильтрации
        if resident_id or block or q:
            query = query.outerjoin(Resident, Resident.id == Notification.resident_id)
            if block:
                query = query.outerjoin(Block, Block.id == Resident.block_id)
        
        # Фильтр по статусу
        if status and status.upper() in {s.value for s in NotificationStatus}:
            status_enum = NotificationStatus(status.upper())
            query = query.filter(Notification.status == status_enum)
        
        # Фильтр по резиденту
        if resident_id:
            query = query.filter(Notification.resident_id == resident_id)
        
        # Фильтр по блоку
        if block:
            query = query.filter(Block.name == block)
        
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
            
            result.append({
                "id": notif.id,
                "user_id": notif.user_id,
                "resident_id": notif.resident_id,
                "message": notif.message,
                "status": notif.status.value,
                "created_at": notif.created_at.isoformat(),
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "user_full_name": notif.user.full_name,
                "user_phone": notif.user.phone,
                "user_email": notif.user.email,
                "resident_code": resident_code,
                "resident_info": resident_info,
                "block_name": block_name,
                "unit_number": unit_number,
            })
        
        return {
            "notifications": result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "last_page": last_page,
            }
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/{notification_id}/json", response_model=dict)
def get_notification_json_public(
    notification_id: int,
    db: Session = Depends(get_db),
):
    """JSON endpoint для получения одного уведомления (публичный, без авторизации)."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return JSONResponse({"error": "Notification not found"}, status_code=404)
    
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
    
    return {
        "id": notif.id,
        "user_id": notif.user_id,
        "resident_id": notif.resident_id,
        "message": notif.message,
        "status": notif.status.value,
        "created_at": notif.created_at.isoformat(),
        "read_at": notif.read_at.isoformat() if notif.read_at else None,
        "user_full_name": notif.user.full_name,
        "user_phone": notif.user.phone,
        "user_email": notif.user.email,
        "resident_code": resident_code,
        "resident_info": resident_info,
        "block_name": block_name,
        "unit_number": unit_number,
    }


@router.delete("/{notification_id}/json")
def delete_notification_json(
    notification_id: int,
    db: Session = Depends(get_db),
):
    """JSON endpoint для удаления уведомления (публичный, без авторизации)."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return JSONResponse({"error": "Notification not found"}, status_code=404)
    
    db.delete(notif)
    db.commit()
    
    return {"ok": True, "message": "Notification deleted"}

