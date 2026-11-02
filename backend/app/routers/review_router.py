from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models import Inspection, Batch, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/review", tags=["review"])


class ReviewAction(BaseModel):
    result: str  # ok or defective
    defect_type_id: int | None = None
    notes: str = ""


@router.get("/queue")
def get_review_queue(
    plant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(Inspection).where(Inspection.result == "review", Inspection.reviewed == False)
    if plant_id:
        batch_ids = [b.id for b in session.exec(select(Batch).where(Batch.plant_id == plant_id)).all()]
        if batch_ids:
            query = query.where(Inspection.batch_id.in_(batch_ids))
        else:
            return []
    elif user.role != "admin":
        batch_ids = [b.id for b in session.exec(select(Batch).where(Batch.plant_id == user.plant_id)).all()]
        if batch_ids:
            query = query.where(Inspection.batch_id.in_(batch_ids))
        else:
            return []
    return session.exec(query.order_by(Inspection.created_at)).all()


@router.post("/{inspection_id}")
def review_inspection(
    inspection_id: int,
    action: ReviewAction,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    inspection = session.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    inspection.original_result = inspection.result
    inspection.result = action.result
    inspection.defect_type_id = action.defect_type_id
    inspection.review_notes = action.notes
    inspection.reviewed = True
    inspection.reviewer_id = user.id
    session.add(inspection)

    batch = session.get(Batch, inspection.batch_id)
    if batch:
        all_inspections = session.exec(select(Inspection).where(Inspection.batch_id == batch.id)).all()
        batch.passed_count = sum(1 for i in all_inspections if i.result == "ok")
        batch.defective_count = sum(1 for i in all_inspections if i.result == "defective")
        batch.review_pending_count = sum(1 for i in all_inspections if i.result == "review" and not i.reviewed)
        session.add(batch)

    session.commit()
    session.refresh(inspection)
    return inspection
