#!/usr/bin/env python3
"""Seed VisionQC with demo data: plant, lines, shifts, parts, 30 days of batches."""
import os
import sys
import random
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.app.database import init_db, engine
from backend.app.models import (
    User, Plant, Line, PartType, DefectType, Shift, Batch, Inspection,
    CustomerJourney, RetentionKPI, Invoice, ModelVersion,
)
from backend.app.auth import hash_password
from sqlmodel import Session

random.seed(42)


def seed():
    init_db()

    with Session(engine) as session:
        existing = session.get(Plant, 1)
        if existing:
            print("Seed data already exists. Skipping.")
            return

        # Users
        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            full_name="VisionQC Admin",
            role="admin",
        )
        session.add(admin)
        session.flush()

        plant = Plant(
            name="Demo Castings Pvt Ltd",
            location="Hyderabad, Telangana",
            status="monthly_plan",
            billing_plan="monthly",
            setup_fee_paid=True,
        )
        session.add(plant)
        session.flush()

        plant_head = User(
            username="rajesh",
            hashed_password=hash_password("rajesh123"),
            full_name="Rajesh Kumar (Plant Head)",
            role="plant_head",
            plant_id=plant.id,
        )
        supervisor = User(
            username="suresh",
            hashed_password=hash_password("suresh123"),
            full_name="Suresh Reddy (Supervisor)",
            role="supervisor",
            plant_id=plant.id,
        )
        session.add(plant_head)
        session.add(supervisor)
        session.flush()

        # Lines
        line_a = Line(name="Casting Line 1", plant_id=plant.id)
        line_b = Line(name="Casting Line 2", plant_id=plant.id)
        session.add(line_a)
        session.add(line_b)
        session.flush()

        # Shifts
        shift_a = Shift(name="A", start_time="06:00", end_time="14:00", plant_id=plant.id)
        shift_b = Shift(name="B", start_time="14:00", end_time="22:00", plant_id=plant.id)
        shift_c = Shift(name="C", start_time="22:00", end_time="06:00", plant_id=plant.id)
        session.add_all([shift_a, shift_b, shift_c])
        session.flush()

        # Part types
        pt1 = PartType(name="Pump Impeller", description="Cast iron pump impeller", plant_id=plant.id)
        pt2 = PartType(name="Valve Body", description="Brass valve body casting", plant_id=plant.id)
        pt3 = PartType(name="Motor Housing", description="Aluminium motor housing", plant_id=plant.id)
        session.add_all([pt1, pt2, pt3])
        session.flush()

        # Defect types
        dt1 = DefectType(name="Surface Crack", description="Visible crack on casting surface", plant_id=plant.id)
        dt2 = DefectType(name="Porosity", description="Gas holes or shrinkage porosity", plant_id=plant.id)
        dt3 = DefectType(name="Misrun", description="Incomplete filling of mould cavity", plant_id=plant.id)
        dt4 = DefectType(name="Surface Scratch", description="Handling scratch on finished surface", plant_id=plant.id)
        session.add_all([dt1, dt2, dt3, dt4])
        session.flush()

        lines = [line_a, line_b]
        shifts = [shift_a, shift_b, shift_c]
        parts = [pt1, pt2, pt3]
        defects = [dt1, dt2, dt3, dt4]

        # 30 days of batches
        today = datetime(2026, 11, 2, tzinfo=timezone.utc)
        for day_offset in range(30):
            batch_date = today - timedelta(days=29 - day_offset)

            num_batches = random.randint(2, 5)
            for _ in range(num_batches):
                line = random.choice(lines)
                shift = random.choice(shifts)
                part = random.choice(parts)

                total = random.randint(40, 150)
                defect_rate = random.uniform(0.02, 0.15)
                if shift.name == "C":
                    defect_rate *= 1.4
                if part == pt1:
                    defect_rate *= 1.2

                num_defective = max(0, int(total * defect_rate))
                num_ok = total - num_defective

                hour = random.randint(6, 21)
                batch_time = batch_date.replace(hour=hour, minute=random.randint(0, 59))

                batch = Batch(
                    plant_id=plant.id,
                    line_id=line.id,
                    shift_id=shift.id,
                    part_type_id=part.id,
                    created_at=batch_time,
                    status="completed",
                    total_images=total,
                    passed_count=num_ok,
                    defective_count=num_defective,
                )
                session.add(batch)
                session.flush()

                for j in range(min(total, 5)):
                    is_defect = j < min(num_defective, 3)
                    insp = Inspection(
                        batch_id=batch.id,
                        image_path=f"data/uploads/{plant.id}/sample/img_{batch.id}_{j}.jpg",
                        result="defective" if is_defect else "ok",
                        confidence=random.uniform(0.75, 0.99),
                        defect_type_id=random.choice(defects).id if is_defect else None,
                        reviewed=True,
                        created_at=batch_time,
                    )
                    session.add(insp)

        # Customer journey history
        for status, days_ago in [
            ("free_sample_audit", 90),
            ("paid_pilot", 60),
            ("monthly_plan", 30),
        ]:
            entry = CustomerJourney(
                plant_id=plant.id,
                status=status,
                changed_at=today - timedelta(days=days_ago),
                notes=f"Moved to {status.replace('_', ' ')}",
            )
            session.add(entry)

        # Retention KPIs
        for month_offset in range(3):
            month_date = today - timedelta(days=30 * (2 - month_offset))
            kpi = RetentionKPI(
                plant_id=plant.id,
                month=month_date.strftime("%Y-%m"),
                report_open_rate=random.uniform(0.7, 0.95),
                defect_catch_rate=random.uniform(0.80, 0.95),
                churned=False,
            )
            session.add(kpi)

        # Model version
        mv = ModelVersion(
            plant_id=None,
            version="baseline_v1",
            model_path="data/models/baseline_model.pth",
            accuracy=92.5,
            precision=0.91,
            recall=0.88,
            confusion_matrix_json="[[45, 5], [6, 44]]",
            is_active=True,
        )
        session.add(mv)

        session.commit()
        print("Seed data created successfully!")
        print("  Plant: Demo Castings Pvt Ltd, Hyderabad")
        print("  Users: admin/admin123, rajesh/rajesh123, suresh/suresh123")
        print("  Lines: 2, Shifts: 3 (A/B/C), Part types: 3, Defect types: 4")
        print(f"  Historical batches: ~30 days of data")


if __name__ == "__main__":
    seed()
