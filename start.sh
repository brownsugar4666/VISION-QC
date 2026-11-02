#!/bin/bash
set -e

echo "=== VisionQC Setup ==="

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt -q

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

# Generate sample images if no dataset
echo "Setting up dataset..."
python3 scripts/download_dataset.py

# Seed database
echo "Seeding database..."
python3 scripts/seed_data.py

echo ""
echo "=== Starting VisionQC ==="
echo "Backend API: http://localhost:8000"
echo "Frontend:    http://localhost:5173"
echo "API Docs:    http://localhost:8000/docs"
echo ""
echo "On your phone: open http://<your-ip>:5173"
echo ""

# Start backend and frontend
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
