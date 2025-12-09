from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette import status
from pydantic import BaseModel
from ..database import get_db
from ..models import User, RoleEnum
from ..security import verify_password, set_session, clear_session
from ..deps import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    role: str
    username: str
    message: str


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


@router.post("/api/auth/login", response_model=LoginResponse)
async def api_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """API endpoint для логина, возвращает роль пользователя и устанавливает сессию"""
    from fastapi.responses import JSONResponse
    
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Создаем JSONResponse с данными
    response_data = LoginResponse(
        success=True,
        role=user.role.value,
        username=user.username,
        message="Вход выполнен успешно"
    )
    
    # Создаем Response и устанавливаем cookie
    response = JSONResponse(content=response_data.dict())
    set_session(response, user.id)
    
    return response


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
