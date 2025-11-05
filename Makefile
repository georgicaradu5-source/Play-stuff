.PHONY: help lint type test all dev dry-run budget limits peek clean

help:
	@echo "Available targets:"
	@echo "  lint    - Run Ruff checks via nox"
	@echo "  type    - Run mypy on src via nox"
	@echo "  test    - Run pytest with coverage via nox"
	@echo "  all     - Run lint, type, and test via nox"
	@echo "  dev     - Install all dev dependencies"
	@echo "  dry-run - Run agent in dry-run mode (safe)"
	@echo "  budget  - Print current budget status"
	@echo "  limits  - Print current rate limits"
	@echo "  peek    - Show recent actions from DB"
	@echo "  clean   - Remove cache and build artifacts"

lint:
	nox -s lint

type:
	nox -s type

test:
	nox -s test

all:
	nox -s all

dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock nox ruff mypy

dry-run:
	python src/main.py --dry-run --mode both

budget:
	python src/main.py --safety print-budget

limits:
	python src/main.py --safety print-limits

peek:
	python scripts/peek_actions.py --limit 25

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov .nox
