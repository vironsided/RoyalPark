from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from starlette import status
from ..database import get_db
from ..models import User
from ..security import verify_password, set_session, clear_session
from ..deps import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, db: Session = Depends(get_db),
          username: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные учетные данные"}, status_code=400)

    user.last_login_at = datetime.utcnow()
    db.commit()

    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    set_session(resp, user.id)

    if user.require_password_change:
        resp = RedirectResponse(url="/force-change-password", status_code=status.HTTP_302_FOUND)
        set_session(resp, user.id)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    clear_session(resp)
    return resp


@router.get("/force-change-password", response_class=HTMLResponse)
def force_change_password_form(request: Request, user: User = Depends(get_current_user)):
    if not user.require_password_change:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("force_change_password.html", {"request": request})


@router.post("/force-change-password")
def force_change_password(request: Request, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user),
                          new_password: str = Form(...), new_password2: str = Form(...)):
    if new_password != new_password2:
        return templates.TemplateResponse("force_change_password.html", {"request": request, "error": "Пароли не совпадают"}, status_code=400)

    from ..security import hash_password
    user.password_hash = hash_password(new_password)
    user.require_password_change = False
    user.temp_password_plain = None
    user.last_password_change_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(url="/", status_code=302)
