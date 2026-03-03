.PHONY: install test lint pilot sweep

install:
	uv sync --all-extras

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

pilot:
	uv run python scripts/run_pilot.py

sweep:
	uv run python scripts/run_sweep.py
