PYTHON ?= python3
VENV := .venv

.PHONY: setup-venv tests lint format install clean check help
.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  setup-venv  - Create a virtual environment"
	@echo "  update      - Update dependencies, poetry.lock file, and install project"
	@echo "  lint        - Check code with ruff"
	@echo "  format      - Format code with ruff"
	@echo "  tests       - Run tests with pytest"
	@echo "  demo        - Generate a gif demonstrating the TurboDL CLI functionality and upload it to asciinema"
	@echo "  help        - Show this help message"

setup-venv:
	@echo "Creating virtual environment..."
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(VENV)/bin/pip install --upgrade pip
	@$(VENV)/bin/pip install --upgrade poetry
	@touch $(VENV)
	@echo "Virtual environment created at $(VENV) with Poetry installed"

update:
	poetry update
	poetry install

lint:
	poetry run ruff check

format:
	poetry run ruff format

tests:
	poetry run pytest -v --xfail-tb

demo:
	asciinema rec "demo.cast" --overwrite --rows 5 --cols 112 --title "TurboDL CLI Demo (https://github.com/henrique-coder/turbodl)" --command "echo \"$$ turbodl download -cs 700 https://link.testfile.org/300MB /tmp\" && turbodl download -cs 700 https://link.testfile.org/300MB /tmp"
	agg "demo.cast" "assets/demo.gif"
	@echo -n "Do you want to upload the recording to asciinema (y/N): "
	@read answer; if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then asciinema upload "demo.cast"; fi
