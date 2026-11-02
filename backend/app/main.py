import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .routers import (
    auth_router,
    plant_router,
    inspection_router,
    review_router,
    dashboard_router,
    report_router,
    billing_router,
    journey_router,
    validation_router,
    model_router,
)

app = FastAPI(title="VisionQC API", version="1.0.0", description="AI Visual Quality Inspection Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(plant_router.router)
app.include_router(inspection_router.router)
app.include_router(review_router.router)
app.include_router(dashboard_router.router)
app.include_router(report_router.router)
app.include_router(billing_router.router)
app.include_router(journey_router.router)
app.include_router(validation_router.router)
app.include_router(model_router.router)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VisionQC"}
