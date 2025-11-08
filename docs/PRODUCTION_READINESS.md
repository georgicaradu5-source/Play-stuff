---
title: Production Readiness Checklist
---

This document summarizes the operational, security, and quality gates required for this X (Twitter) agent to be production-ready.

## Quality gates

- Build/Typecheck: mypy relaxed profile  -  PASS locally and in CI
- Lint/Style: ruff/flake8 critical checks  -  PASS
- Tests: pytest suite covering auth, rate limiting, storage, telemetry, reliability, client behavior  -  PASS
- Dry-run Safety Gate: `python src/main.py --mode both --dry-run true`  -  PASS; required status check in branch protection

## CI/CD

- Required checks: "Unit Tests (pytest)", "Dry-Run Gate (Safety Validation)"
- Release notes: automated via Release Drafter (drafts on push to `main`)
- Dependency updates: Dependabot for pip and GitHub Actions (weekly)
- Security scanning: CodeQL (weekly + on PR)

## Configuration & Secrets

- Choose auth mode via env `X_AUTH_MODE`: `tweepy` (writes/media) or `oauth2` (reads/dry-run)
- Secrets never committed: `.env`, `.token.json` (ignored); use GitHub Environments or repo secrets
- Optional telemetry: set `ENABLE_TELEMETRY=true` and provide OTLP endpoint vars

## Operations

- Storage: SQLite at `data/agent_unified.db` (action log, rate limits, bandit tables)
- Scheduling: `src/scheduler.py` time windows; safe to dry-run in CI
- Rate limiting: exponential backoff + idempotency on POST; respect `x-rate-limit-reset`

## Runbooks

Local validation

1) Run tests: VS Code task "Run: Tests (pytest -v)"
2) Dry-run end-to-end: VS Code task "Run: Dry-run (both modes)"

Planning & inspection notebooks

Use the strategic inspection notebook to snapshot health and guide contributions:

- Open: `notebooks/Repo_Inspection_and_DryRun.ipynb`
- Before metrics: run `nox -s test` (or `pytest --cov=src --cov-report=xml`) so `coverage.xml` is present
- Clear outputs before commit:
	```bash
	jupyter nbconvert --clear-output --inplace notebooks/Repo_Inspection_and_DryRun.ipynb
	```
- Promote any actionable checklists into GitHub Issues with labels (`improvement`, `telemetry`, `security`, `rate-limit`, `learning`)

Incident quick checks

- Inspect artifacts from CI for budget, rate limits, and DB tail
- Enable telemetry to trace spans around client calls

## Links

- Architecture & components: `docs/X_AGENT_DEEP_DIVE.md`
- Risks & mitigations: `docs/RISK_REGISTER.md`
- Opportunities/backlog: `docs/OPPORTUNITIES.md`
- Assistance/inputs required: `docs/ASSISTANCE_CHECKLIST.md`
