from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models import Plant, Line, PartType, DefectType, Shift, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/plants", tags=["plants"])


class PlantCreate(BaseModel):
    name: str
    location: str


class LineCreate(BaseModel):
    name: str


class PartTypeCreate(BaseModel):
    name: str
    description: str = ""


class DefectTypeCreate(BaseModel):
    name: str
    description: str = ""


class ShiftCreate(BaseModel):
    name: str
    start_time: str
    end_time: str


@router.get("/")
def list_plants(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if user.role == "admin":
        plants = session.exec(select(Plant)).all()
    else:
        plants = session.exec(select(Plant).where(Plant.id == user.plant_id)).all()
    return plants


@router.post("/")
def create_plant(data: PlantCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    plant = Plant(name=data.name, location=data.location)
    session.add(plant)
    session.commit()
    session.refresh(plant)
    return plant


@router.get("/{plant_id}")
def get_plant(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.get("/{plant_id}/lines")
def list_lines(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(Line).where(Line.plant_id == plant_id)).all()


@router.post("/{plant_id}/lines")
def create_line(plant_id: int, data: LineCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    line = Line(name=data.name, plant_id=plant_id)
    session.add(line)
    session.commit()
    session.refresh(line)
    return line


@router.get("/{plant_id}/part-types")
def list_part_types(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(PartType).where(PartType.plant_id == plant_id)).all()


@router.post("/{plant_id}/part-types")
def create_part_type(plant_id: int, data: PartTypeCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    pt = PartType(name=data.name, description=data.description, plant_id=plant_id)
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return pt


@router.get("/{plant_id}/defect-types")
def list_defect_types(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(DefectType).where(DefectType.plant_id == plant_id)).all()


@router.post("/{plant_id}/defect-types")
def create_defect_type(plant_id: int, data: DefectTypeCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    dt = DefectType(name=data.name, description=data.description, plant_id=plant_id)
    session.add(dt)
    session.commit()
    session.refresh(dt)
    return dt


@router.get("/{plant_id}/shifts")
def list_shifts(plant_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return session.exec(select(Shift).where(Shift.plant_id == plant_id)).all()


@router.post("/{plant_id}/shifts")
def create_shift(plant_id: int, data: ShiftCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    shift = Shift(name=data.name, start_time=data.start_time, end_time=data.end_time, plant_id=plant_id)
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


@router.put("/{plant_id}/status")
def update_plant_status(plant_id: int, status: str, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    plant.status = status
    session.add(plant)
    session.commit()
    session.refresh(plant)
    return plant
