.PHONY: setup install dvc-init run-pipeline validate clean help

PYTHON := python3
PIP := pip
VENV_DIR := venv
dvc_remote_dir := /tmp/dvc-remote

help:
	@echo "Available commands:"
	@echo "  make setup         - Create venv, install dependencies, and init DVC (idempotent)"
	@echo "  make install       - Install dependencies in venv"
	@echo "  make dvc-init      - Initialize DVC and configure local remote"
	@echo "  make run-pipeline  - Run DVC pipeline (repro)"
	@echo "  make validate      - Run validation script"
	@echo "  make clean         - Remove venv and temporary files"

setup: $(VENV_DIR)/bin/activate dvc-init

$(VENV_DIR)/bin/activate: requirements.txt
	test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	. $(VENV_DIR)/bin/activate && $(PIP) install -r requirements.txt
	touch $(VENV_DIR)/bin/activate

install: $(VENV_DIR)/bin/activate

dvc-init:
	@if [ ! -d ".dvc" ]; then \
		echo "Initializing DVC..."; \
		if [ -d ".git" ]; then \
			. $(VENV_DIR)/bin/activate && dvc init; \
		else \
			. $(VENV_DIR)/bin/activate && dvc init --no-scm; \
		fi \
	else \
		echo "DVC already initialized."; \
	fi
	@echo "Configuring local remote at $(dvc_remote_dir)..."
	mkdir -p $(dvc_remote_dir)
	. $(VENV_DIR)/bin/activate && dvc remote add -d local-remote $(dvc_remote_dir) -f

run-pipeline: setup
	. $(VENV_DIR)/bin/activate && dvc repro

validate: setup test
	. $(VENV_DIR)/bin/activate && python validation/release_check.py

test: setup
	. $(VENV_DIR)/bin/activate && pip install pytest "httpx<0.28.0" pytest-mock
	. $(VENV_DIR)/bin/activate && pytest tests/ -v


run-api: run-pipeline
	. $(VENV_DIR)/bin/activate && python -m uvicorn inference.app:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@echo "Starting frontend at http://localhost:8080..."
	cd frontend && $(PYTHON) -m http.server 8080

clean:
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache
