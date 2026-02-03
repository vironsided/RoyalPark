import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Enum, Boolean, DateTime, ForeignKey, UniqueConstraint, 
    Numeric, Text, Table, Column, Date
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base




# Связка: пользователь-житель ↔ объекты-резиденты (дома/виллы)
user_residents = Table(
    "user_residents",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("resident_id", ForeignKey("residents.id", ondelete="CASCADE"), primary_key=True),
)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"       # черновик (до выставления)
    ISSUED = "ISSUED"     # выставлен (есть срок оплаты)
    PARTIAL = "PARTIAL"   # частично оплачен
    PAID = "PAID"         # полностью оплачен
    OVERPAID = "OVERPAID" # переплата (редко)
    CANCELED = "CANCELED" # отменён

#Енумы для ролей
class RoleEnum(str, enum.Enum):
    ROOT = "ROOT"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    RESIDENT = "RESIDENT"

#Енумы типов счётчиков
class MeterType(str, enum.Enum):
    ELECTRIC = "ELECTRIC"
    GAS = "GAS"
    WATER = "WATER"
    SEWERAGE = "SEWERAGE"
    SERVICE = "SERVICE"
    RENT = "RENT"
    CONSTRUCTION = "CONSTRUCTION"



#Енумы для типо владельцев
class CustomerType(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    LEGAL = "LEGAL"

class ResidentType(str, enum.Enum):
    OWNER = "OWNER"            # Частный дом (владелец)
    TENANT = "TENANT"          # Арендатор
    SUBTENANT = "SUBTENANT"    # Субарендатор
    OFFICE = "OFFICE"          # Офис

class ResidentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# ----- PaymentMethod -----
class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    ONLINE = "ONLINE"
    ADVANCE = "ADVANCE"    # Оплата из внутреннего аванса резидента

# ----- Payment / PaymentApplication -----
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    resident_id = Column(ForeignKey("residents.id", ondelete="RESTRICT"), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    amount_total = Column(Numeric(12, 2), nullable=False)
    method = Column(SAEnum(PaymentMethod, name="payment_method"), nullable=False)
    reference = Column(String(120), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    created_by_id = Column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)

    resident = relationship("Resident", lazy="joined")
    created_by = relationship("User", lazy="joined")
    applications = relationship(
        "PaymentApplication",
        back_populates="payment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def applied_total(self) -> Decimal:
        # генератор целиком в скобках, стартовое значение — Decimal("0")
        return sum(((a.amount_applied or Decimal("0")) for a in (self.applications or [])), Decimal("0"))

    @property
    def leftover(self) -> Decimal:
        return (self.amount_total or Decimal("0")) - self.applied_total


class PaymentApplication(Base):
    __tablename__ = "payment_applications"
    # УБИРАЕМ уникальное ограничение, чтобы разрешить несколько применений одного платежа к одному счету
    # Это нужно для того, чтобы каждое "Погасить из аванса" создавало отдельную строку в invoice details

    id = Column(Integer, primary_key=True)
    payment_id = Column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False)
    amount_applied = Column(Numeric(12, 2), nullable=False)
    reference = Column(String(100), nullable=True) # "ADVANCE" or "DIRECT"
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    payment = relationship("Payment", back_populates="applications")
    invoice = relationship("Invoice", lazy="joined")



class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False, default=RoleEnum.RESIDENT)

    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Требуется смена пароля (первый вход / сброс):
    require_password_change: Mapped[bool] = mapped_column(Boolean, default=True)

    # Для локальной системы — хранить временный пароль открытым текстом (как просили):
    temp_password_plain: Mapped[str | None] = mapped_column(String(128), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_password_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by = relationship("User", remote_side=[id], lazy="joined")

    # Привязанные дома (только для пользователей-Жителей)
    resident_links: Mapped[list["Resident"]] = relationship(
        "Resident",
        secondary=user_residents,
        back_populates="tenant_links",
        lazy="selectin",
    )

class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("name", name="uq_blocks_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], lazy="joined")

# --- НОВЫЕ ТАБЛИЦЫ ---
class Tariff(Base):
    __tablename__ = "tariffs"
    __table_args__ = (
        UniqueConstraint("name", "meter_type", "customer_type", name="uq_tariffs_name_scope"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    meter_type: Mapped[MeterType] = mapped_column(Enum(MeterType), nullable=False)
    customer_type: Mapped[CustomerType] = mapped_column(Enum(CustomerType), nullable=False)
    vat_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0..100
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    steps: Mapped[list["TariffStep"]] = relationship(
        "TariffStep",
        back_populates="tariff",
        cascade="all, delete-orphan",
        order_by="TariffStep.from_value.asc()",
    )


class TariffStep(Base):
    __tablename__ = "tariff_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id", ondelete="CASCADE"), nullable=False)

    # Числовые границы (для большинства типов)
    from_value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    to_value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    # Датированные границы (для строительных услуг)
    from_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    to_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="steps")

# --- НОВЫЕ ТАБЛИЦЫ ---
class Resident(Base):
    __tablename__ = "residents"
    __table_args__ = (
        UniqueConstraint("block_id", "unit_number", name="uq_resident_block_unit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id", ondelete="RESTRICT"), nullable=False)
    block: Mapped["Block"] = relationship("Block", lazy="joined")

    unit_number: Mapped[str] = mapped_column(String(64), nullable=False)  # номер дома/квартиры в блоке
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    resident_type: Mapped[ResidentType] = mapped_column(Enum(ResidentType), nullable=False, default=ResidentType.OWNER)
    customer_type: Mapped[CustomerType] = mapped_column(Enum(CustomerType), nullable=False, default=CustomerType.INDIVIDUAL)
    status: Mapped[ResidentStatus] = mapped_column(Enum(ResidentStatus), nullable=False, default=ResidentStatus.ACTIVE)

    owner_full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    owner_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    owner_email: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    meters: Mapped[list["ResidentMeter"]] = relationship(
        "ResidentMeter",
        back_populates="resident",
        cascade="all, delete-orphan",
        order_by="ResidentMeter.id.asc()",
        lazy="selectin",  # Используем selectin вместо default, чтобы избежать дубликатов при JOIN
    )

    tenant_links: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_residents,
        back_populates="resident_links",
        lazy="selectin",
    )


class ResidentMeter(Base):
    __tablename__ = "resident_meters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id", ondelete="CASCADE"), nullable=False)
    resident: Mapped["Resident"] = relationship("Resident", back_populates="meters")

    meter_type: Mapped[MeterType] = mapped_column(Enum(MeterType), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # Опорное показание: если счётчик Б/У — вводим текущие показания; если новый — 0.
    initial_reading: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)

    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False)
    tariff: Mapped["Tariff"] = relationship("Tariff", lazy="selectin")  # Исправлено: selectin вместо joined для избежания дубликатов

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- НОВОЕ: показания, логи, счета ---

class MeterReading(Base):
    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resident_meter_id: Mapped[int] = mapped_column(ForeignKey("resident_meters.id", ondelete="CASCADE"), nullable=False)
    resident_meter = relationship("ResidentMeter", lazy="joined")

    reading_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    consumption: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False)
    tariff = relationship("Tariff", lazy="joined")

    amount_net: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)   # без НДС
    vat_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    amount_vat: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    amount_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")


class ReadingLog(Base):
    __tablename__ = "reading_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)   # CREATE / UPDATE / DELETE
    reading_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # может быть None, если удалили
    resident_meter_id: Mapped[int] = mapped_column(ForeignKey("resident_meters.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    
    # Relationships
    resident_meter: Mapped["ResidentMeter"] = relationship("ResidentMeter", lazy="joined")
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id], lazy="joined")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id", ondelete="CASCADE"), nullable=False)
    resident = relationship("Resident", lazy="joined")

    number = Column(String(64), nullable=True, index=True)  # человеко-читаемый №, например "2025-10/000123"
    status = Column(SAEnum(InvoiceStatus, name="invoice_status"), nullable=False, default=InvoiceStatus.DRAFT)
    due_date = Column(Date, nullable=True)  # срок оплаты
    notes = Column(Text, nullable=True)  # примечание для клиента

    period_year: Mapped[int] = mapped_column(Integer, nullable=False)  # например, 2025
    period_month: Mapped[int] = mapped_column(Integer, nullable=False) # 1..12

    amount_net: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    amount_vat: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    amount_total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.id.asc()",
    )

    __table_args__ = (
        UniqueConstraint("resident_id", "period_year", "period_month", name="uq_invoice_resident_period"),
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")

    # ДОЛЖНО БЫТЬ nullable=True
    meter_reading_id: Mapped[int | None] = mapped_column(
        ForeignKey("meter_readings.id", ondelete="CASCADE"),
        nullable=True
    )
    meter_reading: Mapped["MeterReading"] = relationship("MeterReading", lazy="joined")

    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_net: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_vat: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class ResidentService(Base):
    """
    Фикс-ежемесячные услуги резидента (без показаний):
    - SERVICE  : Технические услуги
    - RENT     : Аренда
    """
    __tablename__ = "resident_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    resident_id: Mapped[int] = mapped_column(ForeignKey("residents.id", ondelete="CASCADE"), nullable=False)
    resident: Mapped["Resident"] = relationship("Resident", lazy="joined")

    service_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'SERVICE' | 'RENT'
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    vat_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], lazy="joined")


class NotificationStatus(str, enum.Enum):
    UNREAD = "UNREAD"
    READ = "READ"


class NotificationType(str, enum.Enum):
    INVOICE = "INVOICE"  # Уведомление о выставленном счете
    NEWS = "NEWS"        # Уведомление о новости
    APPEAL = "APPEAL"    # Обращение (существующий тип для обращений)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resident_id: Mapped[int | None] = mapped_column(ForeignKey("residents.id", ondelete="SET NULL"), nullable=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status"),
        default=NotificationStatus.UNREAD,
        nullable=False,
    )
    
    # Новые поля для типа уведомления и связанного объекта
    notification_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # INVOICE, NEWS, APPEAL
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ID счета, новости и т.д.
    
    # Используем функцию из .utils (импорт внутри метода или через default)
    # Но проще изменить default на текущее время Баку в самом приложении
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    user: Mapped["User"] = relationship("User", lazy="joined")
    resident: Mapped["Resident"] = relationship("Resident", lazy="joined")


class News(Base):
    """
    Новости для отображения пользователям.
    Поддерживает мультиязычность через JSON поля.
    """
    __tablename__ = "news"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Мультиязычные поля в TEXT формате ( JSON)
    
    title: Mapped[str] = mapped_column(Text, nullable=False)  
    content: Mapped[str] = mapped_column(Text, nullable=False)  
    
    
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default='info')  
    icon_color: Mapped[str] = mapped_column(String(50), nullable=False, default='#667eea')  
    
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  
    
    
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")


class QRToken(Base):
    """
    Одноразовые QR-токены для установки пароля новыми пользователями.
    """
    __tablename__ = "qr_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_qr_tokens_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    user: Mapped["User"] = relationship("User", lazy="joined")


class PaymentLog(Base):
    """
    Логи всех процессов, связанных с платежами.
    """
    __tablename__ = "payment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    resident_id: Mapped[int | None] = mapped_column(ForeignKey("residents.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, APPLY, ADJUST, ADVANCE_USE
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    payment: Mapped["Payment"] = relationship("Payment", foreign_keys=[payment_id], lazy="joined")
    resident: Mapped["Resident"] = relationship("Resident", foreign_keys=[resident_id], lazy="joined")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="joined")
