.PHONY: help lint type test all

help:
	@echo "Available targets:"
	@echo "  lint  - Run Ruff checks via nox"
	@echo "  type  - Run mypy on src via nox"
	@echo "  test  - Run pytest with coverage via nox"
	@echo "  all   - Run lint, type, and test via nox"

lint:
	nox -s lint

type:
	nox -s type

test:
	nox -s test

all:
	nox -s all
