.PHONY: install setup seed train run backend frontend test clean

install:
	pip3 install -r requirements.txt
	cd frontend && npm install

setup: install
	python3 scripts/download_dataset.py
	python3 scripts/seed_data.py

seed:
	python3 scripts/seed_data.py

train:
	python3 model/train.py

run:
	@echo "Starting VisionQC..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
	cd frontend && npm run dev &
	wait

backend:
	python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

test:
	python3 -m pytest tests/ -v

clean:
	rm -f data/visionqc.db
	rm -rf data/uploads/*
	rm -rf data/models/*.pth
