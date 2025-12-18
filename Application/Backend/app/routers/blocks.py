# app/api/routers/blocks.py
"""
Module: Blocks management (CRUD for villa "blocks"/streets)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-25

Purpose:
    HTML-роуты управления "блоками/улицами" жилого комплекса:
    - список блоков
    - создание
    - переименование
    - удаление
    Всё построено по PRG-паттерну (POST → Redirect → GET), чтобы избежать повторной отправки форм.

Tech stack:
    - FastAPI (routers + Jinja2 templates)
    - SQLAlchemy 2.x ORM (Session + select())
    - Starlette statuses (корректные коды 303 для POST-редиректов)

Conventions:
    - Право доступа: только ROOT/ADMIN
    - Проверка уникальности: регистр-независимо (LOWER(name))
    - Ошибки и успех передаются через query (?error=..., ?ok=...) и показываются в шаблоне

DB note:
    Рекомендую добавить уникальный индекс в БД на lower(name),
    чтобы не положиться только на проверку в приложении:

        -- PostgreSQL (миграция Alembic — см. ниже подсказку)
        CREATE UNIQUE INDEX IF NOT EXISTS blocks_name_ci_uq ON blocks (lower(name));

"""

from __future__ import annotations

from typing import Optional
import logging

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette import status

# Локальные зависимости и модели
from ..database import get_db                        # фабрика Session для DI
from ..deps import get_current_user, require_any_role
from ..models import User, RoleEnum, Block

# Инициализируем логгер для модуля
logger = logging.getLogger(__name__)

# Роутер этого модуля. Тег пригодится для автодока и группировки.
router = APIRouter(prefix="/blocks", tags=["blocks"])

# Подключаем Jinja2 с указанием каталога шаблонов
templates = Jinja2Templates(directory="app/templates")


def _see_other(url: str) -> RedirectResponse:
    """
    Унифицированный редирект для обработки POST-запросов.

    Почему 303:
        После успешного POST корректно перенаправлять на GET с кодом 303 See Other,
        чтобы браузер не пытался повторить POST при F5.
    """
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def list_blocks(
    request: Request,
    user: User = Depends(get_current_user),        # текущий пользователь для шаблона/шапки
    db: Session = Depends(get_db),                 # сессия БД через DI
):
    """
    Страница со списком всех блоков (для ROOT/ADMIN).

    Возвращает:
        HTML со списком блоков (упорядочены по id по возрастанию).
    """
    # SQLAlchemy 2.x: пишем через select() и извлекаем ORM-объекты через .scalars()
    blocks = db.execute(select(Block).order_by(Block.id.asc())).scalars().all()

    # Пробрасываем в шаблон служебные флаги из query для показа флеш-сообщений
    return templates.TemplateResponse(
        "blocks.html",
        {
            "request": request,                    # обязателен для Jinja2Templates в FastAPI
            "user": user,                          # используем в шапке/меню
            "blocks": blocks,                      # данные таблицы
            "ok": request.query_params.get("ok"),  # например: created/renamed/deleted
            "error": request.query_params.get("error"),  # например: empty/exists/notfound/server
        },
    )


@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def create_block(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    name: str = Form(..., description="Название блока/улицы"),  # берём поле из HTML-формы
):
    """
    Создаёт новый блок, если имя непустое и ещё не занято (без учёта регистра).
    """
    # Чистим и нормализуем ввод
    name = (name or "").strip()
    if not name:
        # Пустое имя — возвращаемся на список с ошибкой
        return _see_other("/blocks?error=empty")

    # Проверка уникальности с учётом регистра (LOWER(name))
    exists = db.execute(
        select(Block.id).where(func.lower(Block.name) == func.lower(name))
    ).first()
    if exists:
        return _see_other("/blocks?error=exists")

    try:
        # Создаём ORM-объект и фиксируем автора
        b = Block(name=name, created_by_id=user.id)
        db.add(b)
        db.commit()  # транзакция: INSERT + COMMIT

        logger.info("Block created: id=%s name=%r by user_id=%s", b.id, b.name, user.id)
        return _see_other("/blocks?ok=created")
    except Exception as exc:
        # Неудача — откатываем транзакцию и логируем стек
        db.rollback()
        logger.exception("Failed to create block %r: %s", name, exc)
        return _see_other("/blocks?error=server")


@router.post(
    "/{block_id}/rename",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def rename_block(
    block_id: int,                                   # путь-параметр блока
    db: Session = Depends(get_db),
    new_name: str = Form(..., description="Новое имя блока"),
):
    """
    Переименовывает блок: новое имя обязательно и должно быть уникальным (без учёта регистра).
    """
    # Входные данные: убираем пробелы и валидируем
    new_name = (new_name or "").strip()
    if not new_name:
        return _see_other("/blocks?error=empty")

    # Достаём блок по первичному ключу
    blk: Optional[Block] = db.get(Block, block_id)
    if not blk:
        return _see_other("/blocks?error=notfound")

    # Проверяем, что среди других блоков такого имени нет
    exists = db.execute(
        select(Block.id).where(
            func.lower(Block.name) == func.lower(new_name),
            Block.id != block_id,                   # исключаем сам блок
        )
    ).first()
    if exists:
        return _see_other("/blocks?error=exists")

    try:
        old_name = blk.name
        blk.name = new_name                         # ORM-модификация
        db.commit()                                 # фиксируем UPDATE

        logger.info("Block renamed: id=%s %r -> %r", block_id, old_name, new_name)
        return _see_other("/blocks?ok=renamed")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to rename block id=%s: %s", block_id, exc)
        return _see_other("/blocks?error=server")


@router.post(
    "/{block_id}/delete",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def delete_block(
    block_id: int,
    db: Session = Depends(get_db),
):
    """
    Удаляет блок по id. Если не найден — возвращает ошибку в список.
    Важно: если есть внешние ключи на Block (например, Villas.block_id),
           БД может запретить удаление — тогда придётся либо каскадом,
           либо предварительно переносить/удалять зависимые записи.
    """
    # Получаем объект
    blk: Optional[Block] = db.get(Block, block_id)
    if not blk:
        return _see_other("/blocks?error=notfound")

    try:
        db.delete(blk)      # помечаем на удаление
        db.commit()         # отправляем DELETE
        logger.info("Block deleted: id=%s name=%r", block_id, blk.name)
        return _see_other("/blocks?ok=deleted")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete block id=%s: %s", block_id, exc)
        return _see_other("/blocks?error=server")
