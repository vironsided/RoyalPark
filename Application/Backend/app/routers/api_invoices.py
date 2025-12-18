from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..database import get_db
from ..models import (
    User, RoleEnum, Block, Resident,
    Invoice, InvoiceStatus, InvoiceLine,
    PaymentApplication, Payment
)
from ..deps import get_current_user


router = APIRouter(prefix="/api/invoices", tags=["invoices-api"])


# Pydantic models
class InvoiceLineOut(BaseModel):
    id: int
    description: str
    amount_net: float
    amount_vat: float
    amount_total: float

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: int
    resident_id: int
    resident_code: str  # "A / 205"
    resident_info: str  # "Блок A, №205"
    block_name: str
    unit_number: str
    number: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    notes: Optional[str] = None
    period_year: int
    period_month: int
    amount_net: float
    amount_vat: float
    amount_total: float
    paid_amount: float = 0.0  # сумма оплат
    created_at: datetime
    lines: List[InvoiceLineOut] = []

    class Config:
        from_attributes = True


def _to_int(val: str | None) -> int | None:
    """Мягкое приведение строкового query-параметра к int."""
    if val is None:
        return None
    v = str(val).strip()
    if v == "":
        return None
    try:
        return int(v)
    except Exception:
        return None


def _list_invoices_internal(
    db: Session,
    block_id: Optional[int] = None,
    resident_id: Optional[int] = None,
    status_val: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    q: Optional[str] = None,
    page: int = 1,
    per_page: int = 25,
):
    """Внутренняя функция для получения списка счетов (без авторизации)."""
    query = db.query(Invoice).join(Resident, Resident.id == Invoice.resident_id).join(Block, Block.id == Resident.block_id)
    
    if block_id:
        query = query.filter(Resident.block_id == block_id)
    if resident_id:
        query = query.filter(Invoice.resident_id == resident_id)
    if status_val and status_val in {s.value for s in InvoiceStatus}:
        query = query.filter(Invoice.status == InvoiceStatus(status_val))
    if year:
        query = query.filter(Invoice.period_year == year)
    if month:
        query = query.filter(Invoice.period_month == month)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Invoice.number.ilike(like), Invoice.notes.ilike(like)))
    
    total = query.count()
    last_page = max(1, (total + per_page - 1) // per_page)
    if page > last_page:
        page = last_page
    
    items = (
        query
        .order_by(Invoice.period_year.desc(), Invoice.period_month.desc(), Invoice.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    
    # Получаем сумму оплат по каждому счёту
    ids = [inv.id for inv in items]
    paid_map = {}
    if ids:
        rows = (
            db.query(PaymentApplication.invoice_id, func.coalesce(func.sum(PaymentApplication.amount_applied), 0))
            .filter(PaymentApplication.invoice_id.in_(ids))
            .group_by(PaymentApplication.invoice_id)
            .all()
        )
        paid_map = {inv_id: float(paid) for inv_id, paid in rows}
    
    # Проверяем и исправляем amount_total для каждого счета, если он не совпадает с суммой строк
    needs_commit = False
    for inv in items:
        lines_sum = db.query(
            func.coalesce(func.sum(InvoiceLine.amount_total), 0)
        ).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        
        if abs(float(inv.amount_total or 0) - float(lines_sum)) > 0.01:
            print(f"DEBUG: Invoice {inv.id} amount_total mismatch! invoice={inv.amount_total}, lines_sum={lines_sum}, fixing...")
            inv.amount_total = Decimal(str(lines_sum))
            net_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_net), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
            vat_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_vat), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
            inv.amount_net = Decimal(str(net_sum))
            inv.amount_vat = Decimal(str(vat_sum))
            needs_commit = True
    
    if needs_commit:
        db.commit()
    
    # Получаем блоки и резидентов для формирования данных
    blocks = {b.id: b for b in db.query(Block).all()}
    
    result = []
    for inv in items:
        resident = inv.resident
        block = blocks.get(resident.block_id)
        
        result.append({
            "id": inv.id,
            "resident_id": inv.resident_id,
            "resident_code": f"{block.name if block else ''} / {resident.unit_number}" if block else resident.unit_number,
            "resident_info": f"Блок {block.name if block else ''}, №{resident.unit_number}" if block else f"№{resident.unit_number}",
            "block_name": block.name if block else "",
            "unit_number": resident.unit_number,
            "number": inv.number,
            "status": inv.status.value,
            "due_date": inv.due_date,
            "notes": inv.notes,
            "period_year": inv.period_year,
            "period_month": inv.period_month,
            "amount_net": float(inv.amount_net),
            "amount_vat": float(inv.amount_vat),
            "amount_total": float(inv.amount_total),
            "paid_amount": paid_map.get(inv.id, 0.0),
            "created_at": inv.created_at,
            "lines": [
                {
                    "id": line.id,
                    "description": line.description,
                    "amount_net": float(line.amount_net),
                    "amount_vat": float(line.amount_vat),
                    "amount_total": float(line.amount_total),
                }
                for line in inv.lines
            ],
        })
    
    return {
        "invoices": result,
        "blocks": [{"id": b.id, "name": b.name} for b in blocks.values()],
        "residents": [
            {"id": r.id, "block_name": blocks.get(r.block_id).name if blocks.get(r.block_id) else "", "unit_number": r.unit_number}
            for r in db.query(Resident).all()
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
        },
    }


@router.get("")
def list_invoices_api(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    block_id: Optional[str] = Query(None),
    resident_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=200),
):
    """Список счетов с фильтрами."""
    block_id_i = _to_int(block_id)
    resident_id_i = _to_int(resident_id)
    year_i = _to_int(year)
    month_i = _to_int(month)
    
    return _list_invoices_internal(
        db, block_id_i, resident_id_i, status, year_i, month_i, q, page, per_page
    )


# Bulk issue models
class BulkIssueRequest(BaseModel):
    action: str  # 'by_block' | 'all'
    block_id: Optional[int] = None
    due_date: Optional[str] = None  # YYYY-MM-DD
    
    @classmethod
    def parse_obj(cls, obj):
        # Ensure block_id is None if it's null in JSON
        if isinstance(obj, dict) and 'block_id' in obj and obj['block_id'] is None:
            obj['block_id'] = None
        return super().parse_obj(obj)


class BulkIssueResponse(BaseModel):
    success: bool
    count: int
    message: str


def _bulk_issue_internal(
    db: Session,
    action: str,
    block_id: Optional[int] = None,
    due_date: Optional[str] = None,
):
    """Внутренняя функция для массового выставления счетов (без авторизации)."""
    if action == "by_block" and not block_id:
        raise HTTPException(status_code=400, detail="Block ID is required for 'by_block' action")
    
    if action not in ("by_block", "all"):
        raise HTTPException(status_code=400, detail="Action must be 'by_block' or 'all'")
    
    print(f"DEBUG bulk_issue: action={action}, block_id={block_id}, due_date={due_date}")
    
    # Query for DRAFT invoices
    query = db.query(Invoice).join(Resident, Resident.id == Invoice.resident_id)\
                             .filter(Invoice.status == InvoiceStatus.DRAFT)
    
    if action == "by_block":
        if not block_id:
            raise HTTPException(status_code=400, detail="Block ID is required for 'by_block' action")
        query = query.filter(Resident.block_id == block_id)
        # Debug: check block name
        block_check = db.query(Block).filter(Block.id == block_id).first()
        print(f"DEBUG: Block ID={block_id}, Block name={block_check.name if block_check else 'NOT FOUND'}")
        
        # Debug: check all residents in this block
        residents_in_block = db.query(Resident).filter(Resident.block_id == block_id).all()
        print(f"DEBUG: Total residents in block {block_check.name if block_check else block_id}: {len(residents_in_block)}")
        for r in residents_in_block[:5]:  # Show first 5
            invoices_for_resident = db.query(Invoice).filter(Invoice.resident_id == r.id).all()
            draft_for_resident = [inv for inv in invoices_for_resident if inv.status == InvoiceStatus.DRAFT]
            print(f"DEBUG:   - Resident ID={r.id}, unit={r.unit_number}, total invoices={len(invoices_for_resident)}, DRAFT={len(draft_for_resident)}")
    else:
        # action == "all" - no block filter needed
        print(f"DEBUG: Processing ALL DRAFT invoices (no block filter)")
    
    # Debug: count before processing
    draft_count = query.count()
    print(f"DEBUG: Found {draft_count} DRAFT invoices for action={action}, block_id={block_id}")
    
    if draft_count == 0:
        return {
            "success": True,
            "count": 0,
            "message": "Нет черновиков для выставления"
        }
    
    # Debug: show sample of DRAFT invoices found
    sample_drafts = query.limit(5).all()
    for inv in sample_drafts:
        print(f"DEBUG:   Sample DRAFT invoice: ID={inv.id}, resident_id={inv.resident_id}, period={inv.period_year}-{inv.period_month:02d}")
    
    # Parse due_date
    due: Optional[date] = None
    if due_date:
        try:
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
            print(f"DEBUG: Parsed due_date: {due}")
        except Exception as e:
            print(f"DEBUG: Failed to parse due_date '{due_date}': {e}")
            due = None
    
    cnt = 0
    invoices_to_process = query.all()
    print(f"DEBUG: Processing {len(invoices_to_process)} invoices")
    
    for inv in invoices_to_process:
        print(f"DEBUG: Processing invoice ID={inv.id}, resident_id={inv.resident_id}, period={inv.period_year}-{inv.period_month:02d}, status={inv.status.value}")
        # Generate invoice number if not exists
        if not inv.number:
            prefix = f"{inv.period_year}-{inv.period_month:02d}"
            last_num = (db.query(Invoice.number)
                          .filter(Invoice.period_year == inv.period_year,
                                  Invoice.period_month == inv.period_month,
                                  Invoice.number.ilike(f"{prefix}/%"))
                          .order_by(Invoice.number.desc())
                          .first())
            if last_num and last_num[0]:
                try:
                    seq = int(last_num[0].split("/")[-1]) + 1
                except Exception:
                    seq = inv.id
            else:
                seq = 1
            inv.number = f"{prefix}/{seq:06d}"
        
        inv.status = InvoiceStatus.ISSUED
        if due:
            inv.due_date = due
        cnt += 1
        print(f"DEBUG: Updated invoice ID={inv.id} to ISSUED, due_date={inv.due_date}")
    
    print(f"DEBUG: Total processed: {cnt} invoices")
    try:
        db.commit()
        print(f"DEBUG: Commit successful")
    except Exception as e:
        print(f"DEBUG: Commit failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit changes: {str(e)}")
    
    return {
        "success": True,
        "count": cnt,
        "message": f"Выставлено счетов: {cnt}"
    }


@router.post("/bulk-issue", response_model=BulkIssueResponse)
def bulk_issue_api(
    data: BulkIssueRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Массовое выставление счетов."""
    print(f"=== DEBUG bulk_issue_api START ===")
    print(f"Received request - action={data.action}, block_id={data.block_id}, due_date={data.due_date}, user={user.username if user else 'None'}")
    try:
        # Normalize block_id: if it's None or 0, set to None
        block_id = data.block_id if data.block_id else None
        result = _bulk_issue_internal(db, data.action, block_id, data.due_date)
        print(f"DEBUG bulk_issue_api: Success - {result}")
        print(f"=== DEBUG bulk_issue_api END (SUCCESS) ===")
        return result
    except HTTPException as he:
        print(f"DEBUG bulk_issue_api: HTTPException - {he.status_code}: {he.detail}")
        print(f"=== DEBUG bulk_issue_api END (HTTPException) ===")
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in bulk_issue_api: {e}")
        print(traceback.format_exc())
        print(f"=== DEBUG bulk_issue_api END (ERROR) ===")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ====== Get invoice details ======
class PaymentOut(BaseModel):
    id: int
    date: date
    method: str
    amount: float
    payment_id: int
    reference: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceDetailOut(BaseModel):
    id: int
    resident_id: int
    resident_code: str  # "A / 205"
    number: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    notes: Optional[str] = None
    period_year: int
    period_month: int
    amount_net: float
    amount_vat: float
    amount_total: float
    paid_amount: float = 0.0
    remaining_amount: float = 0.0
    lines: List[InvoiceLineOut] = []
    payments: List[PaymentOut] = []

    class Config:
        from_attributes = True


def _get_invoice_detail_internal(db: Session, invoice_id: int):
    """Внутренняя функция для получения деталей счета (без авторизации)."""
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    resident = inv.resident
    block = resident.block if resident else None
    
    # Получаем строки счета
    lines = db.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all()
    
    # Получаем оплаты по счету
    apps = (
        db.query(PaymentApplication)
        .join(Payment, Payment.id == PaymentApplication.payment_id)
        .filter(PaymentApplication.invoice_id == inv.id)
        .order_by(Payment.received_at.asc(), Payment.id.asc())
        .all()
    )
    
    print(f"DEBUG INVOICE {invoice_id}: Found {len(apps)} payment applications")
    
    # Пересчитываем amount_total из строк счета на случай, если он устарел
    lines_sum = db.query(
        func.coalesce(func.sum(InvoiceLine.amount_total), 0)
    ).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
    
    # Обновляем amount_total в счете, если он отличается от суммы строк
    if abs(float(inv.amount_total or 0) - float(lines_sum)) > 0.01:
        print(f"DEBUG INVOICE {invoice_id}: amount_total mismatch! invoice.amount_total={inv.amount_total}, lines_sum={lines_sum}, updating...")
        inv.amount_total = Decimal(str(lines_sum))
        # Также пересчитываем net и vat
        net_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_net), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        vat_sum = db.query(func.coalesce(func.sum(InvoiceLine.amount_vat), 0)).filter(InvoiceLine.invoice_id == inv.id).scalar() or 0
        inv.amount_net = Decimal(str(net_sum))
        inv.amount_vat = Decimal(str(vat_sum))
        db.commit()
        print(f"DEBUG INVOICE {invoice_id}: Updated invoice totals: net={inv.amount_net}, vat={inv.amount_vat}, total={inv.amount_total}")
    
    paid_total = db.query(func.coalesce(func.sum(PaymentApplication.amount_applied), 0))\
                   .filter(PaymentApplication.invoice_id == inv.id).scalar() or 0
    remaining = float(inv.amount_total or 0) - float(paid_total)
    
    print(f"DEBUG INVOICE {invoice_id}: paid_total={paid_total}, amount_total={inv.amount_total}, remaining={remaining}, lines_count={len(lines)}")
    
    payments = []
    for app in apps:
        p = app.payment
        payment_data = {
            "id": app.id,
            "date": p.received_at,
            "method": p.method.value,
            "amount": float(app.amount_applied),
            "payment_id": p.id,
            "reference": p.reference,
            "comment": p.comment,
        }
        payments.append(payment_data)
        print(f"DEBUG INVOICE {invoice_id}: Payment app {app.id}: payment_id={p.id}, amount={app.amount_applied}, date={p.received_at}, method={p.method.value}")
    
    print(f"DEBUG INVOICE {invoice_id}: Returning {len(payments)} payments")
    
    return {
        "id": inv.id,
        "resident_id": inv.resident_id,
        "resident_code": f"{block.name if block else ''} / {resident.unit_number}" if block else resident.unit_number,
        "number": inv.number,
        "status": inv.status.value,
        "due_date": inv.due_date,
        "notes": inv.notes,
        "period_year": inv.period_year,
        "period_month": inv.period_month,
        "amount_net": float(inv.amount_net),
        "amount_vat": float(inv.amount_vat),
        "amount_total": float(inv.amount_total),
        "paid_amount": float(paid_total),
        "remaining_amount": remaining,
        "lines": [
            {
                "id": line.id,
                "description": line.description,
                "amount_net": float(line.amount_net),
                "amount_vat": float(line.amount_vat),
                "amount_total": float(line.amount_total),
            }
            for line in lines
        ],
        "payments": payments,
    }


@router.get("/{invoice_id}", response_model=InvoiceDetailOut)
def get_invoice_detail_api(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получение деталей счета."""
    return _get_invoice_detail_internal(db, invoice_id)


# ====== Update invoice ======
class InvoiceUpdateRequest(BaseModel):
    due_date: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None


@router.put("/{invoice_id}")
def update_invoice_api(
    invoice_id: int,
    data: InvoiceUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Обновление счета."""
    return _update_invoice_internal(db, invoice_id, data.due_date, data.notes)


def _update_invoice_internal(db: Session, invoice_id: int, due_date: Optional[str], notes: Optional[str]):
    """Внутренняя функция для обновления счета (без авторизации)."""
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if inv.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELED):
        raise HTTPException(status_code=400, detail="Cannot update PAID or CANCELED invoice")
    
    if notes is not None:
        inv.notes = notes.strip() if notes else None
    
    if due_date is not None:
        if due_date and due_date.strip():
            try:
                inv.due_date = datetime.strptime(due_date.strip(), "%Y-%m-%d").date()
            except Exception as e:
                print(f"Warning: Failed to parse due_date '{due_date}': {e}")
                inv.due_date = None
        else:
            # Empty string or None means clear the due_date
            inv.due_date = None
    
    # Если статус DRAFT и есть due_date, можно автоматически выставить счет
    if inv.status == InvoiceStatus.DRAFT and inv.due_date:
        # Генерируем номер счета, если его нет
        if not inv.number:
            prefix = f"{inv.period_year}-{inv.period_month:02d}"
            last_num = (
                db.query(Invoice.number)
                .filter(
                    Invoice.period_year == inv.period_year,
                    Invoice.period_month == inv.period_month,
                    Invoice.number.ilike(f"{prefix}/%")
                )
                .order_by(Invoice.number.desc())
                .first()
            )
            if last_num and last_num[0]:
                try:
                    seq = int(last_num[0].split("/")[-1]) + 1
                except Exception:
                    seq = inv.id
            else:
                seq = 1
            inv.number = f"{prefix}/{seq:06d}"
        inv.status = InvoiceStatus.ISSUED
    
    db.commit()
    return {"success": True, "message": "Счёт успешно обновлён!"}


# ====== Cancel invoice ======
class InvoiceCancelRequest(BaseModel):
    reason: str


@router.post("/{invoice_id}/cancel")
def cancel_invoice_api(
    invoice_id: int,
    data: InvoiceCancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Отмена счета."""
    return _cancel_invoice_internal(db, invoice_id, data.reason)


def _cancel_invoice_internal(db: Session, invoice_id: int, reason: str):
    """Внутренняя функция для отмены счета (без авторизации)."""
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if inv.status not in (InvoiceStatus.DRAFT, InvoiceStatus.ISSUED):
        raise HTTPException(status_code=400, detail="Can only cancel DRAFT or ISSUED invoices")
    
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required")
    
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    audit_line = f"[CANCELED {stamp}] {reason.strip()}"
    inv.notes = f"{inv.notes}\n{audit_line}" if inv.notes else audit_line
    inv.status = InvoiceStatus.CANCELED
    
    db.commit()
    return {"success": True, "message": "Счёт отменён!"}


# ====== Reissue invoice ======
class InvoiceReissueRequest(BaseModel):
    due_date: Optional[str] = None  # YYYY-MM-DD
    comment: Optional[str] = None


@router.post("/{invoice_id}/reissue")
def reissue_invoice_api(
    invoice_id: int,
    data: InvoiceReissueRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Выставить счет заново (только для CANCELED)."""
    return _reissue_invoice_internal(db, invoice_id, data.due_date, data.comment)


def _reissue_invoice_internal(db: Session, invoice_id: int, due_date: Optional[str], comment: Optional[str]):
    """Внутренняя функция для повторного выставления счета (без авторизации)."""
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if inv.status != InvoiceStatus.CANCELED:
        raise HTTPException(status_code=400, detail="Can only reissue CANCELED invoices")
    
    # Проверяем, нет ли уже активного счета для этого резидента за тот же период
    exists_active = db.query(Invoice.id).filter(
        Invoice.resident_id == inv.resident_id,
        Invoice.period_year == inv.period_year,
        Invoice.period_month == inv.period_month,
        Invoice.status != InvoiceStatus.CANCELED,
        Invoice.id != inv.id,
    ).first()
    if exists_active:
        raise HTTPException(status_code=400, detail="Active invoice already exists for this period")
    
    # Обновляем due_date если указан
    if due_date and due_date.strip():
        try:
            inv.due_date = datetime.strptime(due_date.strip(), "%Y-%m-%d").date()
        except Exception as e:
            print(f"Warning: Failed to parse due_date '{due_date}': {e}")
    
    # Генерируем номер счета, если его нет
    if not inv.number:
        prefix = f"{inv.period_year}-{inv.period_month:02d}"
        last_num = (
            db.query(Invoice.number)
            .filter(
                Invoice.period_year == inv.period_year,
                Invoice.period_month == inv.period_month,
                Invoice.number.ilike(f"{prefix}/%")
            )
            .order_by(Invoice.number.desc())
            .first()
        )
        if last_num and last_num[0]:
            try:
                seq = int(last_num[0].split("/")[-1]) + 1
            except Exception:
                seq = inv.id
        else:
            seq = 1
        inv.number = f"{prefix}/{seq:06d}"
    
    # Добавляем запись в примечания
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    line = f"[REISSUED {stamp}] {comment.strip()}" if comment and comment.strip() else f"[REISSUED {stamp}]"
    inv.notes = f"{inv.notes}\n{line}" if inv.notes else line
    
    # Меняем статус на ISSUED
    inv.status = InvoiceStatus.ISSUED
    
    db.commit()
    return {"success": True, "message": "Счёт выставлен заново!"}

