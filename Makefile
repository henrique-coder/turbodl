PYTHON ?= python
VENV := .venv

FIRST_TARGET := $(firstword $(MAKECMDGOALS))
ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

.PHONY: lint format install tests demo help %
.DEFAULT_GOAL := help

lint:
	uv run npx prettier --check "**/*.{html,css,js,md,json,yaml}"
	uv run ruff check .

format:
	uv run npx prettier --write "**/*.{html,css,js,md,json,yaml}"
	uv run ruff format .
	uv run ruff check --fix .

install:
	uv sync --upgrade --all-extras --all-groups

tests:
	uv run pytest -v --xfail-tb

demo:
	asciinema rec "demo.cast" --overwrite --rows 5 --cols 144 --title "TurboDL CLI Demo (https://github.com/henrique-coder/turbodl)" --command "echo \"$$ turbodl download -cs 700 https://github.com/henrique-coder/turbospeed-files/releases/download/turbospeed-files/turbospeed-file-300mb.bin /tmp\" && uv run turbodl download -cs 700 https://github.com/henrique-coder/turbospeed-files/releases/download/turbospeed-files/turbospeed-file-300mb.bin /tmp"
	agg "demo.cast" "assets/demo.gif"
	@echo -n "Do you want to upload the recording to asciinema (y/N): "
	@read answer; if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then asciinema upload "demo.cast"; fi

help:
	@echo "Available commands:"
	@echo "  lint       - Check code with 'prettier' and 'ruff'"
	@echo "  format     - Format code with 'prettier' and 'ruff'"
	@echo "  install    - Install dependencies with 'uv'"
	@echo "  tests      - Run tests with 'pytest'"
	@echo "  demo       - Record a gif demonstrating the TurboDL CLI functionality with 'asciinema' and upload it"
	@echo "  help       - Show this help message"

%:
	@if [ "$(FIRST_TARGET)" = "install" ]; then \
		:; \
	else \
		@echo "make: *** Unknown target '$@'. Use 'make help' for available targets." >&2; \
		exit 1; \
	fi
