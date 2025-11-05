# Sprint Plan and DoD

This summarizes Sprint 1 and 2 scope with acceptance criteria and Definition of Done (DoD).

## Sprint 1 (Governance & CI stabilization)

Scope

- Branch protection with two required checks (tests + dry-run gate)
- CI green: pytest, mypy relaxed, ruff, free-mode dry-run
- Documentation pass: README, quickstart, first tweet guides

Acceptance Criteria

- Both required checks pass on `main`
- Free Mode workflow runs successfully and uploads artifacts

DoD

- Evidence archived under `artifacts/` with run metadata
- M4 completion document updated

## Sprint 2 (Production hardening)

Scope

- Add PR template, Dependabot, Release Drafter, CodeQL, CODEOWNERS
- Production readiness, risk register, deep dive docs
- Close planning issues and consolidate into docs

Acceptance Criteria

- New workflows present and lint clean
- Docs linked from README; issues closed with references

DoD

- CI tasks remain green
- Release draft generated on `main` push
