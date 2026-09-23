BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PYTHON ?= python3.11
IMAGE_NAME ?= knowledge-system

.PHONY: install dev-backend dev-frontend test lint format build up down smoke

# Creates the backend virtual environment, installs both requirement files and the frontend packages.
install: $(VENV)/bin/python
	$(VENV)/bin/pip install -r $(BACKEND_DIR)/requirements.txt -r $(BACKEND_DIR)/requirements-test.txt
	cd $(FRONTEND_DIR) && npm ci

$(VENV)/bin/python:
	$(PYTHON) -m venv $(VENV)

dev-backend:
	cd $(BACKEND_DIR) && .venv/bin/uvicorn main:create_app --factory --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

# Integration tests run too when MONGODB_TEST_URI is set in the environment.
test:
	cd $(BACKEND_DIR) && .venv/bin/pytest
	cd $(FRONTEND_DIR) && npm test

lint:
	cd $(BACKEND_DIR) && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd $(FRONTEND_DIR) && npm run lint && npm run typecheck

format:
	cd $(BACKEND_DIR) && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
	cd $(FRONTEND_DIR) && npm run format

build:
	docker build -t $(IMAGE_NAME) .

up:
	docker compose up --build

down:
	docker compose down

smoke:
	bash scripts/smoke.sh
