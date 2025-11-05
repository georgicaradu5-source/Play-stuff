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

## Reporting Security Issues
Please do not file public issues. Email the maintainers or follow the process in `SECURITY.md`.

## Questions
Open a discussion or issue with the `question` label.
