# Developer entry points. `make check` is what a branch must pass before push.

.PHONY: install install-aws check lint test coverage format

## Install the package in editable mode with the dev tools.
install:
	pip install -e ".[dev]"

## Install the package in editable mode with the aws and dev tools.
install-aws:
	pip install -e ".[dev,aws]"

## Lint and test. This is the gate for every branch.
check: lint test

## Static checks only.
lint:
	ruff check .
	ruff format --check .

## Unit tests only.
test:
	python -m pytest

## Tests with a coverage report for src/iotmal.
coverage:
	python -m pytest --cov --cov-report=term-missing

## Rewrite files to the formatter's style.
format:
	ruff format .
	ruff check --fix .
