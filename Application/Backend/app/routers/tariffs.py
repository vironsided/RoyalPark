# app/api/routers/tariffs.py
"""
Module: Tariffs management (CRUD + JSON)
Author: Mamedli Ayaz
Maintainer: Mamedli Ayaz
Created: 2025-10-25

Purpose:
    Управление тарифами ( Electricity / Gas / Water / SEWERAGE / SERVICE / RENT) c многоступенчатыми интервалами.
    Функционал:
      - список тарифов с фильтрами
      - создание тарифа
      - обновление тарифа (полная замена ступеней)
      - удаление тарифа
      - выдача тарифа в JSON (для модальных форм/JS)

PRG:
    Все POST-запросы завершаются 303 See Other → /tariffs?ok|error=...
    Это защищает от повторной отправки формы после F5.

Validation:
    - name: непустое
    - meter_type: в перечислении MeterType
    - customer_type: в перечислении CustomerType
    - vat_percent: 0..100
    - steps_json: JSON-массив ступеней [{from, to, price}], проверки:
        * from >= 0, price >= 0
        * to > from, либо to = null (бесконечная)
        * интервалы непрерывные (next.from == prev.to)
        * только последняя ступень может быть бесконечной

DB Notes:
    - Рекомендую уникальный индекс на (LOWER(name), meter_type, customer_type):
        CREATE UNIQUE INDEX IF NOT EXISTS tariff_name_ci_uq
            ON tariffs (lower(name), meter_type, customer_type);
    - Для TariffStep полезно добавить индекс по (tariff_id, from_value).

Tech:
    - FastAPI + Jinja2
    - SQLAlchemy 2.x (select/Session)
    - Decimal для цен/объёмов (без float-артефактов)
"""

from __future__ import annotations

from typing import Optional, Iterable, List, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import json
import logging

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette import status

from ..database import get_db
from ..deps import get_current_user, require_any_role
from ..models import (
    User,
    RoleEnum,
    Tariff,
    TariffStep,
    MeterType,
    CustomerType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tariffs", tags=["tariffs"])
templates = Jinja2Templates(directory="app/templates")


# ------------------------------ Helpers ------------------------------------- #

def _see_other(url: str) -> RedirectResponse:
    """Единый 303-редирект для завершения POST-операций."""
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def _to_decimal(value: object) -> Decimal:
    """
    Безопасно приводит вход к Decimal через str, чтобы избежать float-артефактов.
    Генерирует InvalidOperation при невозможности преобразования.
    """
    return Decimal(str(value))


def _parse_steps_json(raw: str) -> List[Tuple[Decimal, Optional[Decimal], Decimal]]:
    """
    Разбирает JSON-массив ступеней тарифа и валидирует непрерывность/порядок.

    Формат входа (строка JSON):
        [
          {"from": 0,    "to": 100,  "price": 0.10},
          {"from": 100,  "to": 500,  "price": 0.15},
          {"from": 500,  "to": null, "price": 0.20}
        ]

    Возвращает:
        Список кортежей (from: Decimal, to: Optional[Decimal], price: Decimal)

    Ошибки:
        ValueError("invalid_json" | "empty_steps" | "infinite_not_last" | "not_continuous"
                   | f"invalid_step_{i}" | f"negative_values_{i}" | f"range_order_{i}")
    """
    # Пытаемся распарсить строку как JSON-массив
    try:
        data = json.loads(raw or "[]")
        assert isinstance(data, list)
    except Exception:
        raise ValueError("invalid_json")

    steps: List[Tuple[Decimal, Optional[Decimal], Decimal]] = []

    for i, item in enumerate(data):
        # Ожидаем словари с ключами from/to/price
        if not isinstance(item, dict):
            raise ValueError(f"invalid_step_{i}")

        try:
            f = _to_decimal(item.get("from"))
            t_raw = item.get("to")
            t = None if (t_raw is None or str(t_raw).strip() == "") else _to_decimal(t_raw)
            p = _to_decimal(item.get("price"))
        except (InvalidOperation, Exception):
            raise ValueError(f"invalid_step_{i}")

        # Значения не должны быть отрицательными
        if f < 0 or p < 0:
            raise ValueError(f"negative_values_{i}")

        # Верхняя граница (если есть) должна быть строго больше нижней
        if t is not None and t <= f:
            raise ValueError(f"range_order_{i}")

        steps.append((f, t, p))

    if not steps:
        raise ValueError("empty_steps")

    # Непрерывность и порядок: каждый следующий from == предыдущему to
    for i in range(len(steps) - 1):
        f1, t1, _ = steps[i]
        f2, _t2, _ = steps[i + 1]
        if t1 is None:
            # Бесконечная ступень может быть только последней
            raise ValueError("infinite_not_last")
        if f2 != t1:
            # Дыра или пересечение
            raise ValueError("not_continuous")

    # Последняя может быть бесконечной — дополнительных действий не нужно
    return steps


def _parse_construction_steps_json(raw: str) -> List[Tuple[date, date, Decimal]]:
    """
    Разбор ступеней для строительных услуг (дата-диапазоны).
    Формат:
        [{"from_date": "2025-01-01", "to_date": "2025-03-31", "price": 1000.00}, ...]
    """
    try:
        data = json.loads(raw or "[]")
        assert isinstance(data, list)
    except Exception:
        raise ValueError("invalid_json")

    if not data:
        raise ValueError("empty_steps")

    steps: List[Tuple[date, date, Decimal]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"invalid_step_{i}")

        from_raw = item.get("from_date")
        to_raw = item.get("to_date")
        if not from_raw or not to_raw:
            raise ValueError(f"invalid_dates_{i}")
        try:
            start = datetime.strptime(from_raw, "%Y-%m-%d").date()
            end = datetime.strptime(to_raw, "%Y-%m-%d").date()
        except Exception:
            raise ValueError(f"invalid_dates_{i}")
        if end < start:
            raise ValueError(f"date_order_{i}")

        try:
            price = _to_decimal(item.get("price"))
        except (InvalidOperation, Exception):
            raise ValueError(f"invalid_step_{i}")
        if price < 0:
            raise ValueError(f"negative_values_{i}")

        steps.append((start, end, price))

    return steps


# ------------------------------ Views --------------------------------------- #

@router.get(
    "/",
    response_class=HTMLResponse,
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def list_tariffs(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    meter: Optional[str] = None,     # фильтр по типу счётчика
    ctype: Optional[str] = None,     # фильтр по типу клиента
    q: Optional[str] = None,         # поиск по имени (ILIKE)
):
    """
    Страница со списком тарифов + фильтры по meter/customer + поиск по имени.
    """
    query = db.execute(select(Tariff)).scalars()

    # Фильтр по типу счётчика, только допустимые значения
    if meter in {m.value for m in MeterType}:
        query = [t for t in query if t.meter_type == MeterType(meter)]

    # Фильтр по типу клиента
    if ctype in {c.value for c in CustomerType}:
        query = [t for t in query if t.customer_type == CustomerType(ctype)]

    # Поиск по имени (регистронезависимо). Через Python, чтобы не усложнять пример;
    # при больших данных лучше перенести в SQL (ilike).
    if q:
        needle = q.strip().lower()
        query = [t for t in query if needle in t.name.lower()]

    # Сортировка по id по возрастанию
    tariffs = sorted(query, key=lambda t: t.id)

    return templates.TemplateResponse(
        "tariffs.html",
        {
            "request": request,
            "user": user,
            "tariffs": tariffs,
            "meter": meter or "",
            "ctype": ctype or "",
            "q": q or "",
            "MeterType": MeterType,         # передаём Enum в шаблон
            "CustomerType": CustomerType,
            "ok": request.query_params.get("ok"),
            "error": request.query_params.get("error"),
        },
    )


@router.post(
    "/create",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def create_tariff(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    name: str = Form(...),
    meter_type: str = Form(...),
    customer_type: str = Form(...),
    vat_percent: int = Form(...),
    steps_json: str = Form(...),
):
    """
    Создание тарифа с валидацией входных полей и разбором ступеней.
    """
    # Базовая валидация полей формы
    name = (name or "").strip()
    if not name:
        return _see_other("/tariffs?error=empty_name")
    if meter_type not in {m.value for m in MeterType}:
        return _see_other("/tariffs?error=bad_meter")
    if customer_type not in {c.value for c in CustomerType}:
        return _see_other("/tariffs?error=bad_customer")
    if not (0 <= int(vat_percent) <= 100):
        return _see_other("/tariffs?error=bad_vat")

    # Разбор ступеней
    is_construction = meter_type == MeterType.CONSTRUCTION.value
    try:
        if is_construction:
            steps = _parse_construction_steps_json(steps_json)
        else:
            steps = _parse_steps_json(steps_json)
    except ValueError as e:
        return _see_other(f"/tariffs?error=steps_{e}")

    # Уникальность имени внутри пары (meter_type, customer_type), регистронезависимо
    exists = db.execute(
        select(Tariff.id).where(
            func.lower(Tariff.name) == func.lower(name),
            Tariff.meter_type == MeterType(meter_type),
            Tariff.customer_type == CustomerType(customer_type),
        )
    ).first()
    if exists:
        return _see_other("/tariffs?error=exists")

    try:
        # Создаём тариф
        t = Tariff(
            name=name,
            meter_type=MeterType(meter_type),
            customer_type=CustomerType(customer_type),
            vat_percent=int(vat_percent),
            created_by_id=user.id,
        )
        db.add(t)
        db.flush()  # получаем t.id до коммита

        # Добавляем ступени
        if is_construction:
            for start, end, price in steps:
                db.add(
                    TariffStep(
                        tariff_id=t.id,
                        from_value=None,
                        to_value=None,
                        from_date=start,
                        to_date=end,
                        price=price,
                    )
                )
        else:
            for f, to, p in steps:
                db.add(
                    TariffStep(
                        tariff_id=t.id,
                        from_value=f,
                        to_value=to,
                        from_date=None,
                        to_date=None,
                        price=p,
                    )
                )

        db.commit()
        logger.info("Tariff created: id=%s name=%r by user_id=%s", t.id, t.name, user.id)
        return _see_other("/tariffs?ok=created")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create tariff %r: %s", name, exc)
        return _see_other("/tariffs?error=server")


@router.get(
    "/{tariff_id}/json",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def get_tariff_json(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    """
    Возвращает тариф и его ступени в JSON (для заполнения формы редактирования).
    """
    t: Optional[Tariff] = db.get(Tariff, tariff_id)
    if not t:
        return JSONResponse({"error": "notfound"}, status_code=status.HTTP_404_NOT_FOUND)

    # Преобразуем Decimal → float только для JSON-ответа
    payload = {
        "id": t.id,
        "name": t.name,
        "meter_type": t.meter_type.value,
        "customer_type": t.customer_type.value,
        "vat_percent": t.vat_percent,
    }
    if t.meter_type == MeterType.CONSTRUCTION:
        payload["steps"] = [
            {
                "from_date": s.from_date.isoformat() if s.from_date else "",
                "to_date": s.to_date.isoformat() if s.to_date else "",
                "price": float(s.price),
            }
            for s in t.steps
        ]
    else:
        payload["steps"] = [
            {
                "from": float(s.from_value),
                "to": (None if s.to_value is None else float(s.to_value)),
                "price": float(s.price),
            }
            for s in t.steps
        ]
    return payload


@router.post(
    "/{tariff_id}/update",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def update_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    meter_type: str = Form(...),
    customer_type: str = Form(...),
    vat_percent: int = Form(...),
    steps_json: str = Form(...),
):
    """
    Полное обновление тарифа: базовые поля + полная замена списка ступеней.
    """
    t: Optional[Tariff] = db.get(Tariff, tariff_id)
    if not t:
        return _see_other("/tariffs?error=notfound")

    # Базовая валидация
    name = (name or "").strip()
    if not name:
        return _see_other("/tariffs?error=empty_name")
    if meter_type not in {m.value for m in MeterType}:
        return _see_other("/tariffs?error=bad_meter")
    if customer_type not in {c.value for c in CustomerType}:
        return _see_other("/tariffs?error=bad_customer")
    if not (0 <= int(vat_percent) <= 100):
        return _see_other("/tariffs?error=bad_vat")

    # Разбор ступеней
    is_construction = meter_type == MeterType.CONSTRUCTION.value
    try:
        if is_construction:
            steps = _parse_construction_steps_json(steps_json)
        else:
            steps = _parse_steps_json(steps_json)
    except ValueError as e:
        return _see_other(f"/tariffs?error=steps_{e}")

    # Проверяем уникальность имени в рамках новой пары типов
    exists = db.execute(
        select(Tariff.id).where(
            Tariff.id != t.id,
            func.lower(Tariff.name) == func.lower(name),
            Tariff.meter_type == MeterType(meter_type),
            Tariff.customer_type == CustomerType(customer_type),
        )
    ).first()
    if exists:
        return _see_other("/tariffs?error=exists")

    try:
        # Обновляем шапку тарифа
        t.name = name
        t.meter_type = MeterType(meter_type)
        t.customer_type = CustomerType(customer_type)
        t.vat_percent = int(vat_percent)

        # Полная замена ступеней:
        # 1) Удаляем старые (bulk delete)
        db.query(TariffStep).filter(TariffStep.tariff_id == t.id).delete()
        # 2) Вставляем новые по текущему порядку
        if is_construction:
            for start, end, price in steps:
                db.add(
                    TariffStep(
                        tariff_id=t.id,
                        from_value=None,
                        to_value=None,
                        from_date=start,
                        to_date=end,
                        price=price,
                    )
                )
        else:
            for f, to, p in steps:
                db.add(
                    TariffStep(
                        tariff_id=t.id,
                        from_value=f,
                        to_value=to,
                        from_date=None,
                        to_date=None,
                        price=p,
                    )
                )

        db.commit()
        logger.info("Tariff updated: id=%s name=%r", t.id, t.name)
        return _see_other("/tariffs?ok=updated")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update tariff id=%s: %s", tariff_id, exc)
        return _see_other("/tariffs?error=server")


@router.post(
    "/{tariff_id}/delete",
    dependencies=[Depends(require_any_role(RoleEnum.ROOT, RoleEnum.ADMIN))],
)
def delete_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
):
    """
    Удаляет тариф целиком. Если есть внешние зависимости (например, инвойсы с ссылкой на тариф),
    БД может запретить удаление — в таком случае продумать политику:
      - запрет удаления, если есть использования (вернуть ?error=linked),
      - soft-delete (флаг active=false),
      - либо каскад, если бизнес-правильно.
    """
    t: Optional[Tariff] = db.get(Tariff, tariff_id)
    if not t:
        return _see_other("/tariffs?error=notfound")

    try:
        db.delete(t)
        db.commit()
        logger.info("Tariff deleted: id=%s name=%r", t.id, t.name)
        return _see_other("/tariffs?ok=deleted")
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete tariff id=%s: %s", tariff_id, exc)
        return _see_other("/tariffs?error=server")
