from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette import status
from ..database import get_db
from ..models import User, RoleEnum
from ..deps import get_current_user, can_manage_user
from ..utils import generate_temp_password
from ..security import hash_password
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/users")
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def list_users(request: Request, actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "actor": actor,
        "user": actor,
        "users": users
    })


@router.post("/create")
def create_user(request: Request, actor: User = Depends(get_current_user), db: Session = Depends(get_db),
                username: str = Form(...),
                role: RoleEnum = Form(...)):
    if actor.role == RoleEnum.ADMIN and role in (RoleEnum.ROOT, RoleEnum.ADMIN):
        return RedirectResponse(url="/users?error=Недостаточно прав", status_code=302)

    temp_pass = generate_temp_password(10)
    user = User(
        username=username,
        password_hash=hash_password(temp_pass),
        role=role,
        require_password_change=True,
        temp_password_plain=temp_pass,
        created_by_id=actor.id,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/users?ok=created", status_code=302)


@router.post("/{user_id}/reset")
def reset_password(user_id: int, actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        return RedirectResponse(url="/users?error=notfound", status_code=302)

    if not can_manage_user(target, actor):
        return RedirectResponse(url="/users?error=forbidden", status_code=302)

    temp_pass = generate_temp_password(10)
    target.password_hash = hash_password(temp_pass)
    target.require_password_change = True
    target.temp_password_plain = temp_pass
    db.commit()
    return RedirectResponse(url="/users?ok=reset", status_code=302)


@router.post("/{user_id}/rename")
def rename_user(user_id: int, new_username: str = Form(...),
                actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        return RedirectResponse(url="/users?error=notfound", status_code=302)
    if not can_manage_user(target, actor):
        return RedirectResponse(url="/users?error=forbidden", status_code=302)
    target.username = new_username
    db.commit()
    return RedirectResponse(url="/users?ok=renamed", status_code=302)


@router.post("/{user_id}/delete")
def delete_user(user_id: int, actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        return RedirectResponse(url="/users?error=notfound", status_code=302)
    if target.id == actor.id:
        return RedirectResponse(url="/users?error=cannot_delete_self", status_code=302)
    if not can_manage_user(target, actor):
        return RedirectResponse(url="/users?error=forbidden", status_code=302)
    db.delete(target)
    db.commit()
    return RedirectResponse(url="/users?ok=deleted", status_code=302)
