# Contributing to Play-stuff

Thanks for your interest in contributing! This repo powers a production-ready X (Twitter) agent. To keep things reliable and safe, please follow these guidelines.

## Ground Rules
- Use GitHub issues for bugs/requests; link PRs to issues.
- All changes must go through Pull Requests.
- CI must pass: tests, type checks, lint, and dry-run gate.
- Never commit secrets. `.env` and `.token.json` are ignored.
- For new X API endpoints, always go through `XClient` and `UnifiedAuth`.

## Development Workflow
1. Fork and create a feature branch from `main`.
2. Write tests for new behavior (both auth modes when relevant).
3. Run locally:
   - Tests: `pytest -v`
   - Type check: `./scripts/mypy.ps1`
   - Dry-run: `python src/main.py --mode both --dry-run true`
4. Commit with clear messages and open a PR.

## Commit Message Tips
- Use short, imperative subject: "Fix: handle 429 retry jitter"
- Include context and links to issues.

## Coding Standards
- Python 3.11+
- Keep imports clean; run `ruff` (CI enforces style).
- Respect architecture boundaries (see README and docs).

## CI and Coverage

All PRs must pass CI checks:
- **Lint**: `ruff check .` (critical errors only in flake8 job)
- **Type check**: `mypy src`
- **Tests**: `pytest -q --cov=src --cov-fail-under=50`
- **Coverage**: Must meet or exceed 50% threshold (currently at 55.99%)

Coverage reports are uploaded to Codecov and as CI artifacts:
- View coverage trends at [Codecov](https://codecov.io/gh/georgicaradu5-source/Play-stuff)
- Download coverage XML artifacts from CI runs (retention: 30 days)

To run the full CI validation locally:
```bash
pytest -q --cov=src --cov-report=xml --cov-report=term --cov-fail-under=50
python scripts/check_ascii.py --scan-dirs src docs
ruff check .
mypy src
```

## Pre-commit Hooks

This repo uses pre-commit hooks to enforce code quality. After setup, hooks run automatically on commit:
- **ruff**: Format and lint
- **mypy**: Type checking
- **pytest**: Run fast unit tests

Install pre-commit (included in dev dependencies):
```bash
pip install pre-commit
pre-commit install
```

## Reporting Security Issues
Please do not file public issues. Email the maintainers or follow the process in `SECURITY.md`.


## Troubleshooting: Windows pre-commit /bin/sh warning

If you see an error like `/bin/sh: not found` or similar when committing on Windows, it's because pre-commit expects a Unix shell. To resolve:

- **Recommended:** Use Git Bash as your terminal when working with this repo. This ensures all hooks run as intended.
- **Alternative:** If you must use PowerShell or CMD, you can bypass hooks with `git commit --no-verify` (not recommended for regular development).

If you have questions or run into issues, open a discussion or issue with the `question` label.
