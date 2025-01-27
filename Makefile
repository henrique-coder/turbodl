PYTHON ?= python3
VENV := .venv

.PHONY: setup-venv tests lint format install clean check help
.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  setup-venv  - Create a virtual environment"
	@echo "  install     - Update dependencies, poetry.lock file, and install project"
	@echo "  update      - Update dependencies and poetry.lock file"
	@echo "  lint        - Check code with ruff"
	@echo "  format      - Format code with ruff"
	@echo "  tests       - Run tests with pytest"
	@echo "  help        - Show this help message"

setup-venv:
	@echo "Creating virtual environment..."
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(VENV)/bin/pip install -U pip
	@$(VENV)/bin/pip install -U poetry
	@touch $(VENV)
	@echo "Virtual environment created at $(VENV) with Poetry installed"

install:
	poetry lock
	poetry install

update:
	poetry update

lint:
	poetry run ruff check

format:
	poetry run ruff format

tests:
	poetry run pytest -v
