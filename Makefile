PYTHON ?= python
VENV := .venv

FIRST_TARGET := $(firstword $(MAKECMDGOALS))
ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

.PHONY: install lint format tests demo help %
.DEFAULT_GOAL := help

install:
	uv sync --all-extras --all-groups

lint:
	npx prettier --check "**/*.{html,css,js,md,json,yaml}"
	ruff check .

format:
	npx prettier --write "**/*.{html,css,js,md,json,yaml}"
	ruff check --fix .
	ruff format .

tests:
	uv run pytest -v --xfail-tb

demo:
	asciinema rec "demo.cast" --overwrite --rows 5 --cols 112 --title "TurboDL CLI Demo (https://github.com/henrique-coder/turbodl)" --command "echo \"$$ turbodl download -cs 700 https://link.testfile.org/300MB /tmp\" && uv run turbodl download -cs 700 https://link.testfile.org/300MB /tmp"
	agg "demo.cast" "assets/demo.gif"
	@echo -n "Do you want to upload the recording to asciinema (y/N): "
	@read answer; if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then asciinema upload "demo.cast"; fi

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  lint       - Check code with ruff"
	@echo "  format     - Format code with ruff"
	@echo "  tests      - Run tests with pytest"
	@echo "  demo       - Generate a gif demonstrating the TurboDL CLI functionality"
	@echo "  help       - Show this help message"

%:
	@if [ "$(FIRST_TARGET)" = "install" ]; then \
		:; \
	else \
		@echo "make: *** Unknown target '$@'. Use 'make help' for available targets." >&2; \
		exit 1; \
	fi
