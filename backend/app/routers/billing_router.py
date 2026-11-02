from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session
from ..models import Batch, Invoice, Plant, Line, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])

BATCH_FEE = 500
MONTHLY_PER_LINE = 15000
SETUP_FEE = 10000
FIXED_COST_MONTHLY = 30000
VARIABLE_PER_LINE_MONTHLY = 3500


@router.get("/invoice/{plant_id}")
def compute_invoice(
    plant_id: int,
    month: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    year, mon = month.split("-")
    batches = session.exec(
        select(Batch).where(
            Batch.plant_id == plant_id,
            Batch.created_at >= datetime(int(year), int(mon), 1, tzinfo=timezone.utc),
            Batch.created_at < datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc) if int(mon) < 12
            else Batch.created_at < datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc),
        )
    ).all()

    batch_count = len(batches)
    batch_fee_total = batch_count * BATCH_FEE

    lines = session.exec(select(Line).where(Line.plant_id == plant_id, Line.is_active == True)).all()
    num_lines = len(lines)
    monthly_plan_total = num_lines * MONTHLY_PER_LINE

    setup_fee = SETUP_FEE if not plant.setup_fee_paid else 0

    if batch_fee_total <= monthly_plan_total:
        cheaper_plan = "per_batch"
        total = batch_fee_total + setup_fee
    else:
        cheaper_plan = "monthly"
        total = monthly_plan_total + setup_fee

    if plant.billing_plan == "per_batch":
        total = batch_fee_total + setup_fee
    else:
        total = monthly_plan_total + setup_fee

    existing = session.exec(
        select(Invoice).where(Invoice.plant_id == plant_id, Invoice.month == month)
    ).first()
    if existing:
        existing.batch_count = batch_count
        existing.batch_fee_total = batch_fee_total
        existing.monthly_plan_lines = num_lines
        existing.monthly_plan_total = monthly_plan_total
        existing.setup_fee = setup_fee
        existing.total_amount = total
        existing.cheaper_plan = cheaper_plan
        session.add(existing)
        session.commit()
        session.refresh(existing)
        invoice = existing
    else:
        invoice = Invoice(
            plant_id=plant_id,
            month=month,
            batch_count=batch_count,
            batch_fee_total=batch_fee_total,
            monthly_plan_lines=num_lines,
            monthly_plan_total=monthly_plan_total,
            setup_fee=setup_fee,
            total_amount=total,
            cheaper_plan=cheaper_plan,
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)

    return {
        "invoice": invoice,
        "recommendation": f"{'Monthly plan' if cheaper_plan == 'monthly' else 'Per-batch'} is cheaper for this usage ({batch_count} batches across {num_lines} lines).",
        "pricing": {
            "batch_fee": BATCH_FEE,
            "monthly_per_line": MONTHLY_PER_LINE,
            "setup_fee": SETUP_FEE,
        },
    }


@router.get("/unit-economics")
def unit_economics(
    num_lines: int = 3,
    user: User = Depends(get_current_user),
):
    revenue_per_line = MONTHLY_PER_LINE
    variable_per_line = VARIABLE_PER_LINE_MONTHLY
    contribution_per_line = revenue_per_line - variable_per_line
    margin_pct = round(contribution_per_line / revenue_per_line * 100, 1)
    breakeven_lines = FIXED_COST_MONTHLY / contribution_per_line if contribution_per_line > 0 else float("inf")

    total_revenue = num_lines * revenue_per_line
    total_variable = num_lines * variable_per_line
    total_cost = FIXED_COST_MONTHLY + total_variable
    gross_profit = total_revenue - total_cost
    gross_margin = round(gross_profit / total_revenue * 100, 1) if total_revenue > 0 else 0

    return {
        "fixed_cost_monthly": FIXED_COST_MONTHLY,
        "variable_per_line_monthly": VARIABLE_PER_LINE_MONTHLY,
        "revenue_per_line_monthly": MONTHLY_PER_LINE,
        "contribution_per_line": contribution_per_line,
        "contribution_margin_pct": margin_pct,
        "breakeven_lines": round(breakeven_lines, 1),
        "scenario": {
            "num_lines": num_lines,
            "total_revenue": total_revenue,
            "total_variable_cost": total_variable,
            "total_fixed_cost": FIXED_COST_MONTHLY,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "gross_margin_pct": gross_margin,
        },
    }
