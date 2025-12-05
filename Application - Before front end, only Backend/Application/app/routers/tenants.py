# app/api/routers/tenants.py
"""
Module: Tenants (Residents' user accounts)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-30

Purpose:
    - Список/поиск учётных записей Жителей (роль RESIDENT)
    - Пагинация + выбор элементов на страницу (25/50/100)
    - Создание / обновление / сброс пароля / удаление
    - JSON для модалки редактирования

Notes:
    - POST → 303 See Other (PRG-паттерн), как на других страницах.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import User, RoleEnum, Block, Resident
from ..security import hash_password
from ..utils import generate_temp_password
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/tenants", tags=["tenants"])
templates = Jinja2Templates(directory="app/templates")


def _see_other(url: str) -> RedirectResponse:
    """Единый POST->Redirect (303 See Other)."""
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenants_list(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str | None = None,
    block_id: str | None = None,
    unit_number: str | None = None,
    page: int = 1,
    per_page: int = 25,
):
    """
    Список пользователей с ролью RESIDENT + данные для модалки.
    Пагинация: page>=1; per_page в {25,50,100} (защитно ограничиваем до 200).
    """
    # нормализуем
    page = max(1, int(page or 1))
    per_page = int(per_page or 25)
    if per_page not in (25, 50, 100):
        per_page = 25
    per_page = max(1, min(200, per_page))
    unit_number = (unit_number or "").strip()

    block_id_int: int | None = None
    if block_id not in (None, ""):
        try:
            block_id_int = int(block_id)
        except ValueError:
            block_id_int = None

    query = db.query(User).filter(User.role == RoleEnum.RESIDENT)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (User.username.ilike(like))
            | (User.full_name.ilike(like))
            | (User.phone.ilike(like))
            | (User.email.ilike(like))
        )

    if block_id_int:
        query = query.join(User.resident_links).filter(Resident.block_id == block_id_int)
        if unit_number:
            unit_like = f"%{unit_number}%"
            query = query.filter(Resident.unit_number.ilike(unit_like))
        query = query.distinct()
    else:
        unit_number = ""

    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page

    tenants = (
        query.order_by(User.id.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Для модалки — всё как раньше
    blocks = db.query(Block).order_by(Block.name.asc()).all()
    residents = db.query(Resident).order_by(Resident.block_id.asc(), Resident.unit_number.asc()).all()

    # лента страниц вокруг текущей
    window = 2
    pages = [p for p in range(max(1, page - window), min(last_page, page + window) + 1)]

    return templates.TemplateResponse(
        "tenants.html",
        {
            "request": request,
            "user": user,
            "tenants": tenants,
            "blocks": blocks,
            "residents": residents,
            "q": q or "",
            "block_id": block_id_int,
            "unit_number": unit_number,
            # пагинация
            "page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
            "pages": pages,
            "per_page_options": [25, 50, 100],
        },
    )


@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenant_create(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    username: str = Form(...),
    full_name: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    comment: str = Form(""),
    resident_ids: list[int] = Form(default=[]),
):
    """Создать пользователя-жителя и привязать выбранные дома."""
    username = (username or "").strip()
    if not username:
        return _see_other("/tenants?error=empty_username")

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return _see_other("/tenants?error=user_exists")

    temp = generate_temp_password(10)
    u = User(
        username=username,
        password_hash=hash_password(temp),
        role=RoleEnum.RESIDENT,
        require_password_change=True,
        temp_password_plain=temp,
        full_name=(full_name or None),
        phone=(phone or None),
        email=(email or None),
        comment=(comment or None),
    )
    db.add(u)
    db.flush()  # id

    if resident_ids:
        objs = db.query(Resident).filter(Resident.id.in_(resident_ids)).all()
        u.resident_links = objs

    db.commit()
    return _see_other("/tenants?ok=created")


@router.get(
    "/{tenant_id}/json",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenant_json(tenant_id: int, db: Session = Depends(get_db)):
    """Данные для модалки редактирования."""
    u = db.get(User, tenant_id)
    if not u or u.role != RoleEnum.RESIDENT:
        return JSONResponse({"error": "notfound"}, status_code=status.HTTP_404_NOT_FOUND)
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name or "",
        "phone": u.phone or "",
        "email": u.email or "",
        "comment": u.comment or "",
        "resident_ids": [r.id for r in (u.resident_links or [])],
    }


@router.post(
    "/{tenant_id}/update",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenant_update(
    tenant_id: int,
    db: Session = Depends(get_db),
    username: str = Form(...),
    full_name: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    comment: str = Form(""),
    resident_ids: list[int] = Form(default=[]),
):
    """Обновить профиль жителя и набор привязанных домов (полная замена)."""
    u = db.get(User, tenant_id)
    if not u or u.role != RoleEnum.RESIDENT:
        return _see_other("/tenants?error=notfound")

    username = (username or "").strip()
    if not username:
        return _see_other("/tenants?error=empty_username")

    exists = db.query(User).filter(User.id != u.id, User.username == username).first()
    if exists:
        return _see_other("/tenants?error=user_exists")

    u.username = username
    u.full_name = full_name or None
    u.phone = phone or None
    u.email = email or None
    u.comment = comment or None

    objs = db.query(Resident).filter(Resident.id.in_(resident_ids or [])).all()
    u.resident_links = objs

    db.commit()
    return _see_other("/tenants?ok=updated")


@router.post(
    "/{tenant_id}/reset",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenant_reset(tenant_id: int, db: Session = Depends(get_db)):
    """Сбросить пароль (выдать временный, обязать сменить при входе)."""
    u = db.get(User, tenant_id)
    if not u or u.role != RoleEnum.RESIDENT:
        return _see_other("/tenants?error=notfound")
    temp = generate_temp_password(10)
    u.password_hash = hash_password(temp)
    u.require_password_change = True
    u.temp_password_plain = temp
    db.commit()
    return _see_other("/tenants?ok=reset")


@router.post(
    "/{tenant_id}/delete",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN, RoleEnum.OPERATOR))],
)
def tenant_delete(tenant_id: int, db: Session = Depends(get_db)):
    """Удалить учётную запись жителя."""
    u = db.get(User, tenant_id)
    if not u or u.role != RoleEnum.RESIDENT:
        return _see_other("/tenants?error=notfound")
    db.delete(u)
    db.commit()
    return _see_other("/tenants?ok=deleted")
