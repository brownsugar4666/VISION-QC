import os
import json
import subprocess
import sys
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session
from ..models import ModelVersion, User
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/models", tags=["models"])

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..")
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")


@router.get("/versions")
def list_versions(
    plant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(ModelVersion)
    if plant_id is not None:
        query = query.where(ModelVersion.plant_id == plant_id)
    return session.exec(query.order_by(ModelVersion.created_at.desc())).all()


@router.get("/active")
def get_active_model(
    plant_id: int | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    query = select(ModelVersion).where(ModelVersion.is_active == True)
    if plant_id is not None:
        query = query.where(ModelVersion.plant_id == plant_id)
    else:
        query = query.where(ModelVersion.plant_id == None)
    model = session.exec(query.order_by(ModelVersion.created_at.desc())).first()
    if not model:
        return {"message": "No active model found"}
    return model


@router.post("/retrain")
def trigger_retrain(
    plant_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("admin")),
):
    train_script = os.path.join(BASE_DIR, "model", "train.py")
    if not os.path.exists(train_script):
        raise HTTPException(status_code=500, detail="Training script not found")

    try:
        result = subprocess.run(
            [sys.executable, train_script, "--plant-id", str(plant_id)],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=BASE_DIR,
        )
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Training timed out after 10 minutes"}


@router.post("/rollback/{version_id}")
def rollback_model(
    version_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("admin")),
):
    version = session.get(ModelVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    current_active = session.exec(
        select(ModelVersion).where(
            ModelVersion.is_active == True,
            ModelVersion.plant_id == version.plant_id,
        )
    ).all()
    for m in current_active:
        m.is_active = False
        session.add(m)

    version.is_active = True
    session.add(version)
    session.commit()
    return {"message": f"Rolled back to version {version.version}", "model": version}
