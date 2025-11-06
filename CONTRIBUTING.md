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
   - Type check: `./scripts/mypy.ps1` (Windows) or `./scripts/mypy.sh` (Linux/macOS)
   - Dry-run: `python src/main.py --mode both --dry-run true`
   - ASCII check: `python scripts/check_ascii.py --scan-dirs src docs`
4. Commit with clear messages and open a PR.

## CI Workflow and Coverage
- **CI runs on push and PR**: All tests, linting (ruff), type checks (mypy), and coverage validation.
- **Coverage artifacts**: CI uploads coverage reports to Codecov for monitoring trends. Current threshold: 42%.
- **Coverage monitoring**: View coverage details on [Codecov](https://codecov.io/gh/georgicaradu5-source/Play-stuff).
- **Pre-commit hooks**: Optional local hooks for linting and formatting. On Windows, see troubleshooting below.

## Commit Message Tips
- Use short, imperative subject: "Fix: handle 429 retry jitter"
- Include context and links to issues.

## Coding Standards
- Python 3.11+
- Keep imports clean; run `ruff` (CI enforces style).
- Respect architecture boundaries (see README and docs).

## Reporting Security Issues
Please do not file public issues. Email the maintainers or follow the process in `SECURITY.md`.


## Troubleshooting: Windows pre-commit /bin/sh warning

If you see an error like `/bin/sh: not found` or similar when committing on Windows, it's because pre-commit expects a Unix shell. To resolve:

- **Recommended:** Use Git Bash as your terminal when working with this repo. This ensures all hooks run as intended.
- **Alternative:** If you must use PowerShell or CMD, you can bypass hooks with `git commit --no-verify` (not recommended for regular development).

### Common Pre-commit Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `/bin/sh: not found` | Pre-commit needs Unix shell | Use Git Bash or `--no-verify` |
| `ruff: command not found` | Dev dependencies not installed | Run `pip install -e .[dev]` |
| `mypy: command not found` | Dev dependencies not installed | Run `pip install -e .[dev]` |
| Hook runs but fails | Code style/type errors | Fix errors or run `ruff check .` and `mypy src` locally |

If you have questions or run into issues, open a discussion or issue with the `question` label.
