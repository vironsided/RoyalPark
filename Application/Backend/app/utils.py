import secrets
import string
from datetime import datetime, date, time, timedelta, timezone
from typing import Any

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

# Основная таймзона проекта (GMT+4, Asia/Baku). Если нет tzdata — используем фиксированный UTC+4.
def _load_baku_tz():
    if not ZoneInfo:
        return timezone(timedelta(hours=4), name="UTC+4")
    try:
        return ZoneInfo("Asia/Baku")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=4), name="UTC+4")

BAKU_TZ = _load_baku_tz()


def generate_temp_password(length: int = 10) -> str:
    """
    Генерирует случайный пароль заданной длины.
    Использует только буквы (верхний и нижний регистр) и цифры.
    Примеры: fCMLqhzVSb, Kx9mP2vLq, F8nR5wT3Y
    """
    # Используем только буквы и цифры (без специальных символов)
    alphabet = string.ascii_letters + string.digits
    
    # Генерируем случайный пароль из букв и цифр
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def now_baku() -> datetime:
    """
    Текущее время в часовой зоне Азербайджана (GMT+4).
    При отсутствии ZoneInfo используется системное время.
    """
    if BAKU_TZ:
        return datetime.now(BAKU_TZ)
    return datetime.now()


def to_baku_datetime(value: Any) -> datetime:
    """
    Приводит значение к datetime в зоне Asia/Baku.
    Поддерживаются: datetime, date, ISO-строка, None.
    """
    if value is None:
        return now_baku()

    if isinstance(value, datetime):
        if value.tzinfo and BAKU_TZ:
            return value.astimezone(BAKU_TZ)
        if BAKU_TZ:
            return value.replace(tzinfo=BAKU_TZ)
        return value

    if isinstance(value, date):
        base_time = time.min
        if BAKU_TZ:
            return datetime.combine(value, base_time, tzinfo=BAKU_TZ)
        return datetime.combine(value, base_time)

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo and BAKU_TZ:
                return parsed.astimezone(BAKU_TZ)
            if BAKU_TZ:
                return parsed.replace(tzinfo=BAKU_TZ)
            return parsed
        except Exception:
            return now_baku()

    return now_baku()
