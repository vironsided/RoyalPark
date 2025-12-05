from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db
from ..models import (
    User, Resident, Payment, Invoice, Block,
    Notification, NotificationStatus, PaymentMethod
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard-api"])


# Pydantic models
class DashboardStatsOut(BaseModel):
    totalUsers: int
    totalBuildings: int
    totalResidents: int
    monthlyPayments: float
    activeRequests: int
    totalPayments: int
    totalInvoices: int
    unpaidInvoices: int

    class Config:
        from_attributes = True


class RecentPaymentOut(BaseModel):
    id: int
    resident_code: str
    resident_info: str
    amount_total: float
    received_at: date
    method: str
    status: str

    class Config:
        from_attributes = True


class RecentActivityOut(BaseModel):
    id: int
    type: str  # "payment", "invoice", "reading", "notification"
    title: str
    description: str
    time: str
    icon: str  # "success", "warning", "info"

    class Config:
        from_attributes = True


class PaymentChartDataOut(BaseModel):
    labels: List[str]
    data: List[float]
    period: str  # "week", "month", "year"


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
):
    """Получить статистику для dashboard (публичный endpoint)."""
    try:
        # Общее количество пользователей
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        # Общее количество зданий (блоков)
        total_buildings = db.query(func.count(Block.id)).scalar() or 0
        
        # Общее количество резидентов
        total_residents = db.query(func.count(Resident.id)).scalar() or 0
        
        # Платежи за текущий месяц
        now = datetime.utcnow()
        month_start = date(now.year, now.month, 1)
        monthly_payments_query = db.query(func.sum(Payment.amount_total)).filter(
            Payment.received_at >= month_start
        )
        monthly_payments = float(monthly_payments_query.scalar() or 0)
        
        # Активные заявки (непрочитанные уведомления)
        active_requests = db.query(func.count(Notification.id)).filter(
            Notification.status == NotificationStatus.UNREAD
        ).scalar() or 0
        
        # Общее количество платежей
        total_payments = db.query(func.count(Payment.id)).scalar() or 0
        
        # Общее количество счетов
        total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
        
        # Неоплаченные счета (статус не "paid")
        from ..models import InvoiceStatus
        unpaid_invoices = db.query(func.count(Invoice.id)).filter(
            Invoice.status != InvoiceStatus.PAID
        ).scalar() or 0
        
        return DashboardStatsOut(
            totalUsers=total_users,
            totalBuildings=total_buildings,
            totalResidents=total_residents,
            monthlyPayments=monthly_payments,
            activeRequests=active_requests,
            totalPayments=total_payments,
            totalInvoices=total_invoices,
            unpaidInvoices=unpaid_invoices
        )
    except Exception as e:
        return {"error": str(e)}


@router.get("/recent-payments")
def get_recent_payments(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Получить последние платежи (публичный endpoint)."""
    try:
        payments = db.query(Payment).join(Resident, Resident.id == Payment.resident_id).order_by(
            Payment.received_at.desc()
        ).limit(limit).all()
        
        result = []
        for payment in payments:
            block_name = payment.resident.block.name if payment.resident.block else None
            unit_number = payment.resident.unit_number
            resident_code = f"{block_name} / {unit_number}" if block_name and unit_number else "—"
            resident_info = f"Блок {block_name}, №{unit_number}" if block_name and unit_number else "—"
            
            # Определяем статус платежа
            applied_total = sum([app.amount_applied for app in payment.applications], Decimal("0"))
            leftover = payment.amount_total - applied_total
            status = "Оплачено" if leftover <= Decimal("0.01") else "В обработке"
            
            result.append(RecentPaymentOut(
                id=payment.id,
                resident_code=resident_code,
                resident_info=resident_info,
                amount_total=float(payment.amount_total),
                received_at=payment.received_at,
                method=payment.method.value if isinstance(payment.method, PaymentMethod) else (str(payment.method) if payment.method else '—'),
                status=status
            ))
        
        return {"payments": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/recent-activity")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Получить последнюю активность (публичный endpoint)."""
    try:
        activities = []
        
        # Последние платежи
        recent_payments = db.query(Payment).order_by(Payment.received_at.desc()).limit(limit).all()
        for payment in recent_payments:
            block_name = payment.resident.block.name if payment.resident.block else None
            unit_number = payment.resident.unit_number
            resident_info = f"Квартира #{unit_number}" if unit_number else "Квартира"
            if block_name:
                resident_info = f"{resident_info} (Блок {block_name})"
            
            time_ago = get_time_ago(payment.received_at)
            activities.append(RecentActivityOut(
                id=payment.id,
                type="payment",
                title="Новый платеж получен",
                description=f"{resident_info} - ₼{payment.amount_total:.2f}",
                time=time_ago,
                icon="success"
            ))
        
        # Последние уведомления
        recent_notifications = db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
        for notif in recent_notifications:
            time_ago = get_time_ago(notif.created_at)
            activities.append(RecentActivityOut(
                id=notif.id,
                type="notification",
                title="Новое обращение",
                description=notif.message[:50] + "..." if len(notif.message) > 50 else notif.message,
                time=time_ago,
                icon="warning" if notif.status == NotificationStatus.UNREAD else "info"
            ))
        
        # Сортируем по времени (самые новые первые) и берем limit
        activities.sort(key=lambda x: x.id, reverse=True)
        activities = activities[:limit]
        
        return {"activities": activities}
    except Exception as e:
        return {"error": str(e)}


@router.get("/payment-chart")
def get_payment_chart_data(
    period: str = Query("week", regex="^(week|month|year)$"),
    db: Session = Depends(get_db),
):
    """Получить данные для графика платежей (публичный endpoint)."""
    try:
        now = datetime.utcnow()
        labels = []
        data = []
        
        if period == "week":
            # Данные за последние 7 дней
            labels = []
            data = []
            for i in range(6, -1, -1):
                day = now.date() - timedelta(days=i)
                labels.append(day.strftime("%d.%m"))
                
                day_start = datetime.combine(day, datetime.min.time())
                day_end = datetime.combine(day, datetime.max.time())
                
                total = db.query(func.sum(Payment.amount_total)).filter(
                    and_(
                        Payment.received_at >= day_start,
                        Payment.received_at <= day_end
                    )
                ).scalar() or Decimal("0")
                data.append(float(total))
        
        elif period == "month":
            # Данные за последние 4 недели
            labels = []
            data = []
            for i in range(3, -1, -1):
                week_start = now.date() - timedelta(days=(i * 7) + 6)
                week_end = now.date() - timedelta(days=i * 7)
                labels.append(f"Нед {4-i}")
                
                week_start_dt = datetime.combine(week_start, datetime.min.time())
                week_end_dt = datetime.combine(week_end, datetime.max.time())
                
                total = db.query(func.sum(Payment.amount_total)).filter(
                    and_(
                        Payment.received_at >= week_start_dt,
                        Payment.received_at <= week_end_dt
                    )
                ).scalar() or Decimal("0")
                data.append(float(total))
        
        elif period == "year":
            # Данные за последние 12 месяцев
            labels = []
            data = []
            month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
            for i in range(11, -1, -1):
                month_date = now.date() - timedelta(days=30 * i)
                labels.append(month_names[month_date.month - 1])
                
                month_start = date(month_date.year, month_date.month, 1)
                if month_date.month == 12:
                    month_end = date(month_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
                
                month_start_dt = datetime.combine(month_start, datetime.min.time())
                month_end_dt = datetime.combine(month_end, datetime.max.time())
                
                total = db.query(func.sum(Payment.amount_total)).filter(
                    and_(
                        Payment.received_at >= month_start_dt,
                        Payment.received_at <= month_end_dt
                    )
                ).scalar() or Decimal("0")
                data.append(float(total))
        
        return PaymentChartDataOut(
            labels=labels,
            data=data,
            period=period
        )
    except Exception as e:
        return {"error": str(e)}


def get_time_ago(dt: datetime) -> str:
    """Получить строку "X минут/часов/дней назад"."""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} {pluralize(diff.days, 'день', 'дня', 'дней')} назад"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} {pluralize(hours, 'час', 'часа', 'часов')} назад"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} {pluralize(minutes, 'минуту', 'минуты', 'минут')} назад"
    else:
        return "Только что"


def pluralize(n: int, one: str, few: str, many: str) -> str:
    """Русская плюрализация."""
    if n % 10 == 1 and n % 100 != 11:
        return one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return few
    else:
        return many

