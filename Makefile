.PHONY: install format lint test type-check check clean run

install:
	uv sync

format:
	uv run ruff check --select I --fix .
	uv run black .

lint:
	uv run ruff check .

test:
	uv run pytest

type-check:
	uv run mypy src

check: format lint type-check test

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	uv run python -m src
