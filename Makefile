.PHONY: all fix

all:
	poetry run ruff format --check .
	poetry run ruff check .
	poetry run mypy .

fix:
	poetry run ruff format .
	poetry run ruff check --fix .
	poetry run mypy .