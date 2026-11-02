import csv
import io
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from ..database import get_session
from ..models import Batch, Inspection, Line, Shift, PartType, DefectType, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(
    plant_id: int,
    line_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(Batch).where(Batch.plant_id == plant_id)
    if line_id:
        query = query.where(Batch.line_id == line_id)
    if date_from:
        dt_from = datetime.fromisoformat(date_from)
        if dt_from.tzinfo is None:
            dt_from = dt_from.replace(tzinfo=timezone.utc)
        query = query.where(Batch.created_at >= dt_from)
    if date_to:
        dt_to = datetime.fromisoformat(date_to)
        if dt_to.tzinfo is None:
            dt_to = dt_to.replace(tzinfo=timezone.utc)
        query = query.where(Batch.created_at <= dt_to + timedelta(days=1))

    batches = session.exec(query.order_by(Batch.created_at)).all()

    total_images = sum(b.total_images for b in batches)
    total_passed = sum(b.passed_count for b in batches)
    total_defective = sum(b.defective_count for b in batches)

    daily_trend = {}
    for b in batches:
        day = b.created_at.strftime("%Y-%m-%d")
        if day not in daily_trend:
            daily_trend[day] = {"date": day, "total": 0, "defective": 0, "defect_rate": 0}
        daily_trend[day]["total"] += b.total_images
        daily_trend[day]["defective"] += b.defective_count

    for day_data in daily_trend.values():
        if day_data["total"] > 0:
            day_data["defect_rate"] = round(day_data["defective"] / day_data["total"] * 100, 1)

    by_shift = {}
    for b in batches:
        shift = session.get(Shift, b.shift_id)
        sname = shift.name if shift else f"Shift {b.shift_id}"
        if sname not in by_shift:
            by_shift[sname] = {"shift": sname, "total": 0, "defective": 0}
        by_shift[sname]["total"] += b.total_images
        by_shift[sname]["defective"] += b.defective_count

    for s in by_shift.values():
        s["defect_rate"] = round(s["defective"] / s["total"] * 100, 1) if s["total"] > 0 else 0

    by_part = {}
    for b in batches:
        pt = session.get(PartType, b.part_type_id)
        pname = pt.name if pt else f"Part {b.part_type_id}"
        if pname not in by_part:
            by_part[pname] = {"part_type": pname, "total": 0, "defective": 0}
        by_part[pname]["total"] += b.total_images
        by_part[pname]["defective"] += b.defective_count

    for p in by_part.values():
        p["defect_rate"] = round(p["defective"] / p["total"] * 100, 1) if p["total"] > 0 else 0

    batch_ids = [b.id for b in batches]
    by_defect_type = {}
    if batch_ids:
        inspections = session.exec(
            select(Inspection).where(
                Inspection.batch_id.in_(batch_ids),
                Inspection.result == "defective",
            )
        ).all()
        for insp in inspections:
            dt = session.get(DefectType, insp.defect_type_id) if insp.defect_type_id else None
            dname = dt.name if dt else "Unknown"
            by_defect_type[dname] = by_defect_type.get(dname, 0) + 1

    worst_shift = max(by_shift.values(), key=lambda x: x["defect_rate"]) if by_shift else None
    worst_part = max(by_part.values(), key=lambda x: x["defect_rate"]) if by_part else None

    return {
        "total_batches": len(batches),
        "total_images": total_images,
        "total_passed": total_passed,
        "total_defective": total_defective,
        "overall_defect_rate": round(total_defective / total_images * 100, 1) if total_images > 0 else 0,
        "daily_trend": sorted(daily_trend.values(), key=lambda x: x["date"]),
        "by_shift": list(by_shift.values()),
        "by_part": list(by_part.values()),
        "by_defect_type": by_defect_type,
        "worst_shift": worst_shift,
        "worst_part": worst_part,
    }


@router.get("/export-csv")
def export_csv(
    plant_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    batches = session.exec(select(Batch).where(Batch.plant_id == plant_id).order_by(Batch.created_at)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Batch ID", "Date", "Line", "Shift", "Part Type", "Total", "Passed", "Defective", "Defect Rate %"])

    for b in batches:
        line = session.get(Line, b.line_id)
        shift = session.get(Shift, b.shift_id)
        pt = session.get(PartType, b.part_type_id)
        rate = round(b.defective_count / b.total_images * 100, 1) if b.total_images > 0 else 0
        writer.writerow([
            b.id,
            b.created_at.strftime("%Y-%m-%d %H:%M"),
            line.name if line else "",
            shift.name if shift else "",
            pt.name if pt else "",
            b.total_images,
            b.passed_count,
            b.defective_count,
            rate,
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=visionqc_export_plant_{plant_id}.csv"},
    )
