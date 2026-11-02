import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models import Batch, Inspection, User, Plant
from ..auth import get_current_user
from ..services.inference_service import run_inference

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "uploads")


class BatchCreate(BaseModel):
    plant_id: int
    line_id: int
    shift_id: int
    part_type_id: int
    concierge_mode: bool = False


@router.post("/batches")
def create_batch(data: BatchCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    batch = Batch(
        plant_id=data.plant_id,
        line_id=data.line_id,
        shift_id=data.shift_id,
        part_type_id=data.part_type_id,
        concierge_mode=data.concierge_mode,
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)
    return batch


@router.get("/batches")
def list_batches(
    plant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(Batch)
    if plant_id:
        query = query.where(Batch.plant_id == plant_id)
    elif user.role != "admin":
        query = query.where(Batch.plant_id == user.plant_id)
    return session.exec(query.order_by(Batch.created_at.desc())).all()


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    batch = session.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/batches/{batch_id}/inspections")
def get_batch_inspections(batch_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(Inspection).where(Inspection.batch_id == batch_id)).all()


@router.get("/batches/{batch_id}/summary")
def get_batch_summary(batch_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    batch = session.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    inspections = session.exec(select(Inspection).where(Inspection.batch_id == batch_id)).all()

    defect_breakdown = {}
    for insp in inspections:
        if insp.result == "defective" and insp.defect_type_id:
            defect_breakdown[insp.defect_type_id] = defect_breakdown.get(insp.defect_type_id, 0) + 1

    total = len(inspections)
    passed = sum(1 for i in inspections if i.result == "ok")
    defective = sum(1 for i in inspections if i.result == "defective")
    review_pending = sum(1 for i in inspections if i.result == "review")

    return {
        "batch_id": batch_id,
        "total": total,
        "passed": passed,
        "defective": defective,
        "review_pending": review_pending,
        "defect_rate": round(defective / total * 100, 1) if total > 0 else 0,
        "defect_breakdown": defect_breakdown,
    }


@router.post("/batches/{batch_id}/upload")
async def upload_images(
    batch_id: int,
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    batch = session.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    plant_dir = os.path.join(UPLOAD_DIR, str(batch.plant_id), str(batch_id))
    os.makedirs(plant_dir, exist_ok=True)

    results = []
    confidence_threshold = 0.7

    for file in files:
        ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(plant_dir, filename)

        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        rel_path = os.path.relpath(filepath, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

        if batch.concierge_mode:
            inspection = Inspection(
                batch_id=batch_id,
                image_path=rel_path,
                result="review",
                confidence=0.0,
            )
        else:
            result, confidence, gradcam_path, defect_type_id = run_inference(filepath, batch.plant_id)

            if confidence < confidence_threshold:
                final_result = "review"
            else:
                final_result = result

            gc_rel = None
            if gradcam_path:
                gc_rel = os.path.relpath(gradcam_path, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

            inspection = Inspection(
                batch_id=batch_id,
                image_path=rel_path,
                result=final_result,
                confidence=confidence,
                gradcam_path=gc_rel,
                defect_type_id=defect_type_id if result == "defective" else None,
            )

        session.add(inspection)
        session.commit()
        session.refresh(inspection)
        results.append(inspection)

    total_inspections = session.exec(select(Inspection).where(Inspection.batch_id == batch_id)).all()
    batch.total_images = len(total_inspections)
    batch.passed_count = sum(1 for i in total_inspections if i.result == "ok")
    batch.defective_count = sum(1 for i in total_inspections if i.result == "defective")
    batch.review_pending_count = sum(1 for i in total_inspections if i.result == "review")
    session.add(batch)
    session.commit()

    return {"uploaded": len(results), "results": results}


@router.post("/batches/{batch_id}/complete")
def complete_batch(batch_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    batch = session.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    batch.status = "completed"
    session.add(batch)
    session.commit()
    return batch
