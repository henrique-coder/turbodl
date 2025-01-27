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
	@echo "  clean       - Remove cache and temporary files"
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

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache .tox
	rm -rf .coverage coverage.xml
	rm -rf dist build
	rm -rf *.egg-info
	rm -rf .eggs
	rm -rf .pytest_cache
	rm -rf .hypothesis
	rm -rf pip-wheel-metadata
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage.*" -delete
	find . -type f -name "*.so" -delete
