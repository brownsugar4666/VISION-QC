from datetime import datetime, date, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import json


def _utcnow():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: str  # admin, plant_head, supervisor
    plant_id: Optional[int] = Field(default=None, foreign_key="plant.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)


class Plant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str
    status: str = "free_sample_audit"  # free_sample_audit, paid_pilot, monthly_plan
    billing_plan: str = "per_batch"  # per_batch, monthly
    setup_fee_paid: bool = False
    created_at: datetime = Field(default_factory=_utcnow)

    lines: list["Line"] = Relationship(back_populates="plant")
    part_types: list["PartType"] = Relationship(back_populates="plant")
    defect_types: list["DefectType"] = Relationship(back_populates="plant")
    shifts: list["Shift"] = Relationship(back_populates="plant")


class Line(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    plant_id: int = Field(foreign_key="plant.id")
    is_active: bool = True

    plant: Optional[Plant] = Relationship(back_populates="lines")


class PartType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    plant_id: int = Field(foreign_key="plant.id")

    plant: Optional[Plant] = Relationship(back_populates="part_types")


class DefectType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    plant_id: int = Field(foreign_key="plant.id")

    plant: Optional[Plant] = Relationship(back_populates="defect_types")


class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # A, B, C
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    plant_id: int = Field(foreign_key="plant.id")

    plant: Optional[Plant] = Relationship(back_populates="shifts")


class Batch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    line_id: int = Field(foreign_key="line.id")
    shift_id: int = Field(foreign_key="shift.id")
    part_type_id: int = Field(foreign_key="parttype.id")
    created_at: datetime = Field(default_factory=_utcnow)
    status: str = "in_progress"  # in_progress, completed, reviewed
    concierge_mode: bool = False
    total_images: int = 0
    passed_count: int = 0
    defective_count: int = 0
    review_pending_count: int = 0

    inspections: list["Inspection"] = Relationship(back_populates="batch")


class Inspection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    batch_id: int = Field(foreign_key="batch.id")
    image_path: str
    result: str = "pending"  # ok, defective, pending, review
    confidence: float = 0.0
    defect_type_id: Optional[int] = Field(default=None, foreign_key="defecttype.id")
    gradcam_path: Optional[str] = None
    reviewed: bool = False
    reviewer_id: Optional[int] = Field(default=None, foreign_key="user.id")
    original_result: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)

    batch: Optional[Batch] = Relationship(back_populates="inspections")


class ModelVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: Optional[int] = Field(default=None, foreign_key="plant.id")
    version: str
    model_path: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    confusion_matrix_json: str = "[]"
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)

    @property
    def confusion_matrix(self):
        return json.loads(self.confusion_matrix_json)


class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    month: str  # YYYY-MM
    batch_count: int = 0
    batch_fee_total: float = 0.0
    monthly_plan_lines: int = 0
    monthly_plan_total: float = 0.0
    setup_fee: float = 0.0
    total_amount: float = 0.0
    cheaper_plan: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class CustomerJourney(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    status: str  # free_sample_audit, paid_pilot, monthly_plan
    changed_at: datetime = Field(default_factory=_utcnow)
    notes: str = ""


class RetentionKPI(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    month: str  # YYYY-MM
    report_open_rate: float = 0.0
    defect_catch_rate: float = 0.0
    churned: bool = False


class ValidationInterview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    participant_role: str = ""
    business: str = ""
    interview_date: Optional[str] = None
    method: str = ""
    last_defect_incident: str = ""
    cost_frequency: str = ""
    workaround: str = ""
    photos_sent: str = ""
    would_pay: str = ""
    notes: str = ""
