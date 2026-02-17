from __future__ import annotations

import threading
import time
from datetime import timedelta

from sqlalchemy import func

from ..database import SessionLocal
from ..models import (
    Invoice,
    InvoiceStatus,
    PaymentApplication,
    Notification,
    NotificationStatus,
    NotificationType,
    User,
    RoleEnum,
    Resident,
    user_residents,
)
from ..routers.payments import auto_apply_advance
from ..utils import now_baku, to_baku_datetime

# TEMP: shorter values for testing
AUTO_ADVANCE_CHECK_INTERVAL_SEC = 10
AUTO_ADVANCE_GRACE_SECONDS = 30

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _is_due_for_auto(due_date, now_dt) -> bool:
    if not due_date:
        return False
    due_dt = to_baku_datetime(due_date)
    return now_dt >= due_dt + timedelta(seconds=AUTO_ADVANCE_GRACE_SECONDS)


def _build_invoice_label(inv_number: str | None, year: int, month: int) -> str:
    if inv_number:
        return f"{inv_number} ({month:02d}.{year})"
    return f"{month:02d}.{year}"


def _notify_resident_auto_advance(db, resident_id: int, reference_tag: str, total_applied: float) -> None:
    rows = (
        db.query(
            Invoice.id,
            Invoice.number,
            Invoice.period_year,
            Invoice.period_month,
            func.coalesce(func.sum(PaymentApplication.amount_applied), 0)
        )
        .join(PaymentApplication, PaymentApplication.invoice_id == Invoice.id)
        .filter(PaymentApplication.reference == reference_tag)
        .group_by(Invoice.id, Invoice.number, Invoice.period_year, Invoice.period_month)
        .order_by(Invoice.period_year.asc(), Invoice.period_month.asc(), Invoice.id.asc())
        .all()
    )
    if not rows:
        return

    resident = db.get(Resident, resident_id)
    block = resident.block if resident else None
    resident_label = None
    if resident:
        resident_label = f"{block.name if block else ''} / {resident.unit_number}" if block else resident.unit_number

    lines = []
    for inv_id, inv_number, year, month, amount_applied in rows:
        label = _build_invoice_label(inv_number, year, month)
        lines.append(f"{label} — {float(amount_applied):.2f} ₼")

    details = "; ".join(lines)
    message = f"Авто-оплата из аванса: списано {total_applied:.2f} ₼."
    if resident_label:
        message += f" Резидент {resident_label}."
    message += f" Погашены счета: {details}."

    # Notify resident users linked to this resident
    user_ids = (
        db.query(user_residents.c.user_id)
        .filter(user_residents.c.resident_id == resident_id)
        .all()
    )
    user_ids = [row[0] for row in user_ids]
    if not user_ids:
        return

    users = (
        db.query(User)
        .filter(
            User.id.in_(user_ids),
            User.is_active.is_(True),
            User.role == RoleEnum.RESIDENT
        )
        .all()
    )

    for user in users:
        db.add(Notification(
            user_id=user.id,
            resident_id=resident_id,
            message=message,
            status=NotificationStatus.UNREAD,
            notification_type=NotificationType.INVOICE.value,
            related_id=rows[0][0] if len(rows) == 1 else None,
        ))


def _run_once() -> None:
    db = SessionLocal()
    try:
        now_dt = now_baku()
        # Find residents with open invoices and a due date
        rows = (
            db.query(
                Invoice.resident_id,
                func.min(Invoice.due_date).label("min_due"),
            )
            .filter(
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]),
                Invoice.due_date.isnot(None),
            )
            .group_by(Invoice.resident_id)
            .all()
        )

        for resident_id, min_due in rows:
            if not _is_due_for_auto(min_due, now_dt):
                continue
            reference_tag = f"AUTOADV:{resident_id}:{int(now_dt.timestamp())}"
            # Apply available advance to this resident (FIFO)
            affected_count, total_applied = auto_apply_advance(
                db,
                int(resident_id),
                reference_tag=reference_tag
            )
            if affected_count > 0 and total_applied > 0:
                _notify_resident_auto_advance(
                    db,
                    int(resident_id),
                    reference_tag,
                    float(total_applied)
                )

        db.commit()
    except Exception as exc:
        print(f"[auto-advance] failed: {exc}")
        db.rollback()
    finally:
        db.close()


def _loop() -> None:
    while not _stop_event.is_set():
        _run_once()
        _stop_event.wait(AUTO_ADVANCE_CHECK_INTERVAL_SEC)


def start_auto_advance_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_loop, name="auto-advance-scheduler", daemon=True)
    _scheduler_thread.start()


def stop_auto_advance_scheduler() -> None:
    _stop_event.set()
