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


def create_invoice_notification(db, invoice, created_by_user_id=None):
    """
    Создает уведомления для всех пользователей, связанных с резидентом,
    когда выставлен счет с due_date (статус ISSUED).
    """
    from .models import Notification, NotificationStatus, NotificationType, User, user_residents, Invoice, InvoiceStatus
    
    # Проверяем, что счет выставлен (ISSUED) и есть due_date
    if invoice.status.value != "ISSUED" or not invoice.due_date:
        return
    
    # Получаем всех пользователей, связанных с резидентом через M2M таблицу
    users = db.query(User).join(
        user_residents, User.id == user_residents.c.user_id
    ).filter(
        user_residents.c.resident_id == invoice.resident_id,
        User.is_active == True
    ).all()
    
    if not users:
        return
    
    # Получаем информацию о резиденте и блоке
    resident = invoice.resident
    block = resident.block if resident else None
    house_info = f"Блок {block.name if block else ''}, №{resident.unit_number}" if block else f"№{resident.unit_number}"
    
    # Получаем сумму счета
    amount_total = float(invoice.amount_total or 0)
    amount_str = f"{amount_total:.2f} ₼"
    
    # Находим последний счет для этого резидента (с более ранним периодом)
    from sqlalchemy import or_, and_
    last_invoice = db.query(Invoice).filter(
        Invoice.resident_id == invoice.resident_id,
        Invoice.id != invoice.id,
        Invoice.status == InvoiceStatus.ISSUED,
        # Период должен быть раньше текущего
        or_(
            Invoice.period_year < invoice.period_year,
            and_(
                Invoice.period_year == invoice.period_year,
                Invoice.period_month < invoice.period_month
            )
        )
    ).order_by(
        Invoice.period_year.desc(),
        Invoice.period_month.desc()
    ).first()
    
    # Формируем строку периода
    current_period_str = f"{invoice.period_month:02d}.{invoice.period_year}"
    if last_invoice:
        last_period_str = f"{last_invoice.period_month:02d}.{last_invoice.period_year}"
        period_str = f"{last_period_str} - {current_period_str}"
    else:
        period_str = current_period_str
    
    # Форматируем дату для сообщения
    due_date_str = invoice.due_date.strftime("%d.%m.%Y")
    
    message = f"Выставлен счет для {house_info}. Сумма: {amount_str}. Период: {period_str}. Срок оплаты: {due_date_str}"
    
    # Создаем уведомления для каждого пользователя
    for user in users:
        # Проверяем, нет ли уже такого уведомления (чтобы избежать дубликатов)
        existing = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.notification_type == NotificationType.INVOICE.value,
            Notification.related_id == invoice.id,
            Notification.status == NotificationStatus.UNREAD
        ).first()
        
        if not existing:
            notification = Notification(
                user_id=user.id,
                resident_id=invoice.resident_id,
                message=message,
                status=NotificationStatus.UNREAD,
                notification_type=NotificationType.INVOICE.value,
                related_id=invoice.id
            )
            db.add(notification)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating invoice notifications: {e}")


def create_news_notification(db, news):
    """
    Создает уведомления для всех активных пользователей-резидентов
    когда публикуется новая новость.
    """
    from .models import Notification, NotificationStatus, NotificationType, User, RoleEnum
    import json
    
    # Проверяем, что новость активна
    if not news.is_active:
        return
    
    # Проверяем, что published_at установлена и не в будущем
    # Используем небольшой допуск (1 секунда) для учета задержек между операциями
    now = datetime.utcnow()
    if not news.published_at:
        return
    
    # Если published_at в будущем более чем на 1 секунду, не создаем уведомления
    time_diff = (news.published_at - now).total_seconds()
    if time_diff > 1.0:
        return
    
    # Получаем всех активных пользователей-резидентов
    users = db.query(User).filter(
        User.role == RoleEnum.RESIDENT,
        User.is_active == True
    ).all()
    
    if not users:
        return
    
    # Парсим заголовок для сообщения (используем русский по умолчанию)
    try:
        title_data = json.loads(news.title) if isinstance(news.title, str) else news.title
        title_ru = title_data.get('ru', 'Новая новость') if isinstance(title_data, dict) else str(title_data)
    except:
        title_ru = 'Новая новость'
    
    message = f"Опубликована новость: {title_ru}"
    
    # Создаем уведомления для каждого пользователя
    for user in users:
        # Проверяем, нет ли уже такого уведомления
        existing = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.notification_type == NotificationType.NEWS.value,
            Notification.related_id == news.id,
            Notification.status == NotificationStatus.UNREAD
        ).first()
        
        if not existing:
            notification = Notification(
                user_id=user.id,
                resident_id=None,  # Новости не привязаны к конкретному резиденту
                message=message,
                status=NotificationStatus.UNREAD,
                notification_type=NotificationType.NEWS.value,
                related_id=news.id
            )
            db.add(notification)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating news notifications: {e}")
