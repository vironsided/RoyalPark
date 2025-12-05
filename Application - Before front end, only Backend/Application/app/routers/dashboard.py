from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import RoleEnum
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    role_cards = {
        RoleEnum.ROOT: "Вы — ROOT. У вас полный доступ, в том числе к управлению пользователями.",
        RoleEnum.ADMIN: "Вы — Админ. Вы можете управлять Операторами и Резидентами.",
        RoleEnum.OPERATOR: "Вы — Оператор. Доступ к рабочим инструментам оператора.",
        RoleEnum.RESIDENT: "Вы — Резидент. Здесь будет личный кабинет (виджеты счётчиков и оплата).",
    }
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "card_text": role_cards.get(user.role, ""),
    })
