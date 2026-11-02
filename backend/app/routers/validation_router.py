from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from ..database import get_session
from ..models import ValidationInterview, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/validation", tags=["validation"])


class InterviewData(BaseModel):
    participant_role: str = ""
    business: str = ""
    interview_date: str | None = None
    method: str = ""
    last_defect_incident: str = ""
    cost_frequency: str = ""
    workaround: str = ""
    photos_sent: str = ""
    would_pay: str = ""
    notes: str = ""


@router.get("/interviews")
def list_interviews(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    interviews = session.exec(select(ValidationInterview).order_by(ValidationInterview.id)).all()
    return interviews


@router.post("/interviews")
def create_interview(data: InterviewData, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    interview = ValidationInterview(**data.model_dump())
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


@router.put("/interviews/{interview_id}")
def update_interview(interview_id: int, data: InterviewData, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    interview = session.get(ValidationInterview, interview_id)
    if not interview:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Interview not found")
    for key, value in data.model_dump().items():
        setattr(interview, key, value)
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


@router.get("/threshold-check")
def threshold_check(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    interviews = session.exec(select(ValidationInterview)).all()
    total = len(interviews)

    recent_incident = sum(1 for i in interviews if i.last_defect_incident.strip())
    monthly_rejection = sum(1 for i in interviews if "month" in i.cost_frequency.lower() or "weekly" in i.cost_frequency.lower())
    photos_20_plus = sum(1 for i in interviews if i.photos_sent.strip() and _parse_photos(i.photos_sent) >= 20)
    paid_pilot = sum(1 for i in interviews if i.would_pay.lower().strip() in ("yes", "y", "true", "1", "agreed"))

    thresholds = [
        {"metric": "Recent defect incident", "required": f"4 of 5", "actual": f"{recent_incident} of {total}", "met": recent_incident >= 4},
        {"metric": "Monthly rejection/rework", "required": f"3 of 5", "actual": f"{monthly_rejection} of {total}", "met": monthly_rejection >= 3},
        {"metric": "Sent 20+ photos", "required": f"3 of 5", "actual": f"{photos_20_plus} of {total}", "met": photos_20_plus >= 3},
        {"metric": "Agreed to paid pilot", "required": f"1 of 5", "actual": f"{paid_pilot} of {total}", "met": paid_pilot >= 1},
    ]

    all_met = all(t["met"] for t in thresholds)
    some_met = any(t["met"] for t in thresholds)

    if all_met:
        decision = "Proceed"
    elif some_met:
        decision = "Refine"
    else:
        decision = "Pivot"

    return {"thresholds": thresholds, "decision": decision, "total_interviews": total}


def _parse_photos(val: str) -> int:
    try:
        return int("".join(c for c in val if c.isdigit()) or "0")
    except ValueError:
        return 0
