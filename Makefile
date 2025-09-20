# ---- uv Makefile (macOS-friendly) -------------------------------------------
SHELL := /bin/bash
UV ?= uv
PY ?= 3.11
PKG ?= your_package_name

.PHONY: help init venv sync add dev fmt lint type test cov check pre-commit-install pre-commit-run upgrade clean build run

help:
	@echo "Common targets:"
	@echo "  init                 Create venv, sync deps, install pre-commit hook"
	@echo "  venv                 Create .venv with Python $(PY)"
	@echo "  sync                 Install deps from pyproject/uv.lock (all groups)"
	@echo "  add name=PKG         Add a runtime dependency"
	@echo "  dev name=PKG         Add a dev-only dependency"
	@echo "  fmt                  Format with ruff"
	@echo "  lint                 Lint with ruff"
	@echo "  type                 Type-check with mypy"
	@echo "  test                 Run pytest"
	@echo "  cov                  Run pytest with coverage"
	@echo "  check                fmt + lint + type + test"
	@echo "  pre-commit-install   Install git hooks"
	@echo "  pre-commit-run       Run hooks on all files"
	@echo "  upgrade              Re-resolve to latest versions and sync"
	@echo "  build                Build wheel/sdist using hatchling via uv"
	@echo "  run                  Run package as module (python -m $(PKG))"
	@echo "  clean                Remove caches and build artifacts"

init: venv sync pre-commit-install

venv:
	$(UV) venv --python $(PY)

sync:
	$(UV) sync --all-groups

# Usage: make add name=requests
add:
	@test -n "$(name)" || (echo "Usage: make add name=<package>"; exit 1)
	$(UV) add $(name)

# Usage: make dev name=ruff
dev:
	@test -n "$(name)" || (echo "Usage: make dev name=<package>"; exit 1)
	$(UV) add --group dev $(name)

fmt:
	$(UV) run ruff format

lint:
	$(UV) run ruff check .

type:
	$(UV) run mypy

test:
	$(UV) run pytest

cov:
	$(UV) run pytest --cov --cov-report=term-missing

check: fmt lint type test

pre-commit-install:
	$(UV) x pre-commit install

pre-commit-run:
	$(UV) x pre-commit run --all-files

upgrade:
	$(UV) lock --upgrade
	$(UV) sync --all-groups

build:
	$(UV) build

run:
	$(UV) run python -m $(PKG)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov     	       dist build *.egg-info __pycache__ .cache
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
