# VisionQC — AI Visual Quality Inspection Service

A demo-ready web app for AI-powered visual quality inspection of manufactured parts, built for small manufacturers in Telangana. Course project for "Ideation and Business Model Design" (24TU05ET01), Woxsen University.

## Quick Start

```bash
# One command to set up and run everything:
bash start.sh
```

Or step by step:

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Generate sample images (or download Kaggle dataset)
python scripts/download_dataset.py

# 3. (Optional) Train the model
python model/train.py

# 4. Seed demo data
python scripts/seed_data.py

# 5. Start backend + frontend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
cd frontend && npm run dev
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Open on Phone (same Wi-Fi)

Find your IP: `ifconfig | grep "inet "` and open `http://<your-ip>:5173` on your phone.

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | VisionQC Admin |
| rajesh | rajesh123 | Plant Head |
| suresh | suresh123 | Supervisor |

## Features → BMC/Report Mapping

| # | Feature | BMC Block | Report Section |
|---|---------|-----------|----------------|
| 1 | Auth & Roles | Customer Segments (buyer/user/payer) | §6 Block 1 |
| 2 | Plant Setup | Key Resources, Key Activities | §6 Block 6-7 |
| 3 | Batch Inspection + Grad-CAM | Value Proposition (catch defects at line) | §9 Proposed Solution |
| 4 | Human Review Queue + Concierge | Risk R1 mitigation, Validation Plan | §7 Experiment, §11 R1 |
| 5 | Per-Plant Retraining | Moat (model learns plant's parts) | §6 Block 2, Deep Tech |
| 6 | Same-Day Report (PDF + WhatsApp) | Channels, Customer Relationships | §6 Block 3-4 |
| 7 | Dashboard (trends, filters, CSV) | Value Proposition (defect records) | §9 Objectives |
| 8 | Billing & Plans | Revenue Streams, Cost Structure | §6 Block 5, 9; §12 |
| 9 | Customer Journey Tracking | Customer Relationships (onboarding) | §6 Block 4, §10 |
| 10 | Validation Tracker | Validation Plan, Evidence | §7-8 |

## Dataset

The app uses the [Kaggle Casting Product Image Dataset](https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product). To download:

```bash
# Option A: Kaggle CLI
pip install kaggle
kaggle datasets download -d ravirajsinh45/real-life-industrial-dataset-of-casting-product
unzip -o real-life-industrial-dataset-of-casting-product.zip -d data/casting_dataset

# Option B: Manual
# Download from the Kaggle link above and extract to data/casting_dataset/
```

If the dataset is unavailable, `scripts/download_dataset.py` generates synthetic sample images automatically.

## Training

```bash
# Train baseline model on casting dataset / sample images
python model/train.py

# Train plant-specific model
python model/train.py --plant-id 1

# Evaluate
python model/evaluate.py
```

## Testing

```bash
python -m pytest tests/ -v
```

## Project Structure

```
├── backend/
│   └── app/
│       ├── main.py          # FastAPI app
│       ├── models.py         # SQLModel database models
│       ├── auth.py           # JWT authentication
│       ├── database.py       # SQLite connection
│       ├── routers/          # API endpoints
│       │   ├── auth_router.py
│       │   ├── plant_router.py
│       │   ├── inspection_router.py
│       │   ├── review_router.py
│       │   ├── dashboard_router.py
│       │   ├── report_router.py
│       │   ├── billing_router.py
│       │   ├── journey_router.py
│       │   ├── validation_router.py
│       │   └── model_router.py
│       └── services/
│           └── inference_service.py  # Model inference + Grad-CAM
├── frontend/
│   └── src/
│       ├── pages/            # All React page components
│       ├── components/       # Layout, shared components
│       ├── context/          # Auth context
│       └── api.js            # Axios API client
├── model/
│   ├── train.py              # MobileNetV3 transfer learning
│   └── evaluate.py           # Model evaluation + confusion matrix
├── scripts/
│   ├── download_dataset.py   # Dataset download / sample generation
│   └── seed_data.py          # Demo data seeding
├── tests/
│   └── test_api.py           # API and billing tests
├── data/                     # DB, uploads, models (gitignored)
├── requirements.txt
├── Makefile
├── start.sh
└── README.md
```

## 5-Minute Demo Script

1. **Login** as `admin/admin123` — show the dashboard with 30 days of seeded data
2. **Dashboard** — point out defect rate trend, worst shift (C), defects by type pie chart, CSV export
3. **Inspect** — start a new batch, upload 2-3 images, show AI classification with Grad-CAM heatmaps
4. **Review Queue** — show concierge mode: toggle it on, upload images → all go to human review
5. **Reports** — download PDF, click WhatsApp share link
6. **Billing** — show invoice, plan comparison, unit economics slider (break-even at ~3 lines)
7. **Journey** — show pipeline stages Free Audit → Pilot → Monthly
8. **Validation** — add an interview row, show threshold auto-check (Proceed/Refine/Pivot)
9. **Models** — show model versions, accuracy, confusion matrix, retrain button
10. **Phone** — open on phone browser, show camera capture

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLModel (SQLite), PyTorch
- **Frontend:** React 19, Vite, Tailwind CSS v4, Recharts
- **ML:** MobileNetV3-Small (transfer learning), Grad-CAM heatmaps
- **Reports:** ReportLab (PDF), WhatsApp wa.me links
