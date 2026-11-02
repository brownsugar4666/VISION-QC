from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models import CustomerJourney, RetentionKPI, Plant, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/journey", tags=["journey"])


class JourneyUpdate(BaseModel):
    status: str
    notes: str = ""


class KPIUpdate(BaseModel):
    month: str
    report_open_rate: float
    defect_catch_rate: float
    churned: bool = False


@router.get("/{plant_id}")
def get_journey(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    history = session.exec(
        select(CustomerJourney).where(CustomerJourney.plant_id == plant_id).order_by(CustomerJourney.changed_at)
    ).all()
    return {"plant_id": plant_id, "current_status": plant.status, "history": history}


@router.post("/{plant_id}")
def update_journey(
    plant_id: int, data: JourneyUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    plant.status = data.status
    session.add(plant)
    entry = CustomerJourney(plant_id=plant_id, status=data.status, notes=data.notes)
    session.add(entry)
    session.commit()
    return {"status": data.status}


@router.get("/{plant_id}/kpis")
def get_kpis(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    kpis = session.exec(
        select(RetentionKPI).where(RetentionKPI.plant_id == plant_id).order_by(RetentionKPI.month)
    ).all()
    return kpis


@router.post("/{plant_id}/kpis")
def update_kpi(
    plant_id: int, data: KPIUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)
):
    existing = session.exec(
        select(RetentionKPI).where(RetentionKPI.plant_id == plant_id, RetentionKPI.month == data.month)
    ).first()
    if existing:
        existing.report_open_rate = data.report_open_rate
        existing.defect_catch_rate = data.defect_catch_rate
        existing.churned = data.churned
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    kpi = RetentionKPI(
        plant_id=plant_id,
        month=data.month,
        report_open_rate=data.report_open_rate,
        defect_catch_rate=data.defect_catch_rate,
        churned=data.churned,
    )
    session.add(kpi)
    session.commit()
    session.refresh(kpi)
    return kpi
