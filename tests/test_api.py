"""Tests for VisionQC API: auth, billing calculations, and inspection flow."""
import os
import sys
import tempfile
import pytest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_tmpdir = tempfile.mkdtemp()
_test_db = os.path.join(_tmpdir, "test_visionqc.db")
os.environ["VISIONQC_DB"] = _test_db

from sqlmodel import SQLModel, Session, create_engine

test_engine = create_engine(f"sqlite:///{_test_db}", connect_args={"check_same_thread": False})

import backend.app.database as db_mod
db_mod.engine = test_engine

from backend.app.main import app
from backend.app.models import User, Plant, Line, Shift, PartType, DefectType
from backend.app.auth import hash_password

from fastapi.testclient import TestClient
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        admin = User(
            username="testadmin",
            hashed_password=hash_password("test123"),
            full_name="Test Admin",
            role="admin",
            created_at=datetime.now(timezone.utc),
        )
        session.add(admin)
        plant = Plant(
            name="Test Plant",
            location="Test City",
            created_at=datetime.now(timezone.utc),
        )
        session.add(plant)
        session.flush()
        session.add(Line(name="Line 1", plant_id=plant.id))
        session.add(Shift(name="A", start_time="06:00", end_time="14:00", plant_id=plant.id))
        session.add(PartType(name="Test Part", plant_id=plant.id))
        session.add(DefectType(name="Test Defect", plant_id=plant.id))
        session.commit()
    yield
    SQLModel.metadata.drop_all(test_engine)


def get_token():
    r = client.post("/api/auth/login", data={"username": "testadmin", "password": "test123"})
    return r.json()["access_token"]


def auth_header():
    return {"Authorization": f"Bearer {get_token()}"}


class TestAuth:
    def test_login_success(self):
        r = client.post("/api/auth/login", data={"username": "testadmin", "password": "test123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_fail(self):
        r = client.post("/api/auth/login", data={"username": "testadmin", "password": "wrong"})
        assert r.status_code == 401

    def test_me(self):
        r = client.get("/api/auth/me", headers=auth_header())
        assert r.status_code == 200
        assert r.json()["username"] == "testadmin"

    def test_unauthorized(self):
        r = client.get("/api/auth/me")
        assert r.status_code == 401


class TestBilling:
    def test_unit_economics(self):
        r = client.get("/api/billing/unit-economics?num_lines=3", headers=auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["fixed_cost_monthly"] == 30000
        assert data["variable_per_line_monthly"] == 3500
        assert data["revenue_per_line_monthly"] == 15000
        assert data["contribution_per_line"] == 11500
        assert data["breakeven_lines"] == round(30000 / 11500, 1)

    def test_unit_economics_margin(self):
        r = client.get("/api/billing/unit-economics?num_lines=5", headers=auth_header())
        data = r.json()
        scenario = data["scenario"]
        assert scenario["total_revenue"] == 5 * 15000
        assert scenario["total_variable_cost"] == 5 * 3500
        assert scenario["total_cost"] == 30000 + 5 * 3500
        assert scenario["gross_profit"] == scenario["total_revenue"] - scenario["total_cost"]

    def test_invoice(self):
        r = client.get("/api/billing/invoice/1", headers=auth_header())
        assert r.status_code == 200
        data = r.json()
        assert "invoice" in data
        assert "recommendation" in data
        assert "pricing" in data
        assert data["pricing"]["batch_fee"] == 500
        assert data["pricing"]["monthly_per_line"] == 15000
        assert data["pricing"]["setup_fee"] == 10000


class TestPlants:
    def test_list_plants(self):
        r = client.get("/api/plants/", headers=auth_header())
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_plant(self):
        r = client.get("/api/plants/1", headers=auth_header())
        assert r.status_code == 200
        assert r.json()["name"] == "Test Plant"


class TestHealth:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
