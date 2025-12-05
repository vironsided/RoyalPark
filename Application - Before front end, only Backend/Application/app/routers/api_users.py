from typing import List, Optional

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RoleEnum
from ..deps import get_current_user, can_manage_user
from ..security import hash_password
from ..utils import generate_temp_password


router = APIRouter(prefix="/api/users", tags=["users-api"])


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    role: RoleEnum
    is_active: bool
    require_password_change: bool
    temp_password_plain: Optional[str] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    role: RoleEnum = RoleEnum.OPERATOR
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[RoleEnum] = None


@router.get("/", response_model=List[UserOut])
def list_users_api(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    JSON-список пользователей для SPA-админки.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return users


# ВРЕМЕННО: endpoint без авторизации для теста (удалить после настройки авторизации)
@router.get("/public", response_model=List[UserOut])
def list_users_public(
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации между SPA и backend.
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return users


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_api(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Создание пользователя из SPA.
    root может создавать любых, admin — только operator/resident.
    """
    if actor.role == RoleEnum.ADMIN and payload.role in (RoleEnum.ROOT, RoleEnum.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    # генерируем временный пароль (пока без возврата в ответе)
    temp_password = "Temp1234"

    user = User(
        username=payload.username,
        password_hash=hash_password(temp_password),
        role=payload.role,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        require_password_change=True,
        temp_password_plain=temp_password,
        created_by_id=actor.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ВРЕМЕННО: endpoint без авторизации для создания (удалить после настройки авторизации)
@router.post("/public", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_public(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    ВРЕМЕННЫЙ endpoint без авторизации для теста SPA.
    TODO: удалить после настройки нормальной авторизации между SPA и backend.
    """
    temp_password = generate_temp_password(10)
    
    user = User(
        username=payload.username,
        password_hash=hash_password(temp_password),
        role=payload.role,
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        require_password_change=True,
        temp_password_plain=temp_password,
        created_by_id=None,  # нет авторизованного пользователя
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user_api(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Обновление полей пользователя (ФИО, телефон, email, статус, роль).
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if not can_manage_user(user, actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    if payload.username is not None:
        # проверяем дубликаты
        exists = db.query(User).filter(User.username == payload.username, User.id != user.id).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Логин уже используется")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        # admin не может повышать до root/admin
        if actor.role == RoleEnum.ADMIN and payload.role in (RoleEnum.ROOT, RoleEnum.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для смены роли")
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Удаление пользователя.
    """
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if target.id == actor.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить себя")

    if not can_manage_user(target, actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    db.delete(target)
    db.commit()
    return None


# ВРЕМЕННО: публичные endpoints без авторизации (удалить после настройки авторизации)
@router.put("/{user_id}/public", response_model=UserOut)
def update_user_public(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    if payload.username is not None:
        exists = db.query(User).filter(User.username == payload.username, User.id != user.id).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Логин уже используется")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}/public", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_public(
    user_id: int,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    if target.username == 'root':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить root")
    
    db.delete(target)
    db.commit()
    return None


@router.post("/{user_id}/reset/public", response_model=UserOut)
def reset_password_public(
    user_id: int,
    db: Session = Depends(get_db),
):
    """ВРЕМЕННЫЙ endpoint без авторизации для теста."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    if user.username == 'root':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя сбросить пароль root")
    
    temp_password = generate_temp_password(10)
    user.password_hash = hash_password(temp_password)
    user.require_password_change = True
    user.temp_password_plain = temp_password
    
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset", response_model=UserOut)
def reset_password_api(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    """
    Сброс пароля с генерацией временного пароля.
    """
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if not can_manage_user(target, actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    # простой временный пароль (можно заменить на более сложный генератор)
    temp_pass = "Temp1234"
    target.password_hash = hash_password(temp_pass)
    target.require_password_change = True
    target.temp_password_plain = temp_pass
    db.commit()
    db.refresh(target)
    return target


