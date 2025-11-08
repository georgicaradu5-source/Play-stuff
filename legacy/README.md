# Legacy Documentation Archive

This directory contains historical planning documents, deprecated configurations, and superseded files from the project's development phase.

## Contents

### Planning Documents (`planning/`)
Sprint planning, milestone reports, coverage analysis, and implementation tracking from the unified agent development.

**Coverage Campaign (Sprints 1-5):**
- `PHASE_*_COMPLETE.md` — Sprint 1-3 completion reports
- `PHASE_4_PLAN.md` — Final coverage campaign (95.72% → 97.80%)
- `COVERAGE_*.md` — Gap analysis and enhancement tracking
- `M4_TO_M5_TRANSITION.md` — Major version transition notes
- `RELEASE_NOTES_*.md` — Historical release drafts

**Architecture Analysis:**
- `UNIFICATION_PLAN.md` — Original agent merger plan (completed)
- `AGILE_*.md`, `AUTONOMY_*.md` — Design methodology analysis
- `REPOSITORY_ANALYSIS.md` — Codebase structure analysis
- `SPRINT_2_BACKLOG.md` — Sprint 2 planning

**Superseded Documentation:**
- `OBSERVABILITY-root-old.md` → Now `docs/observability/`
- `QUICKSTART-root-old.md` → Now `docs/guides/QUICKSTART.md`
- `READ_BUDGET_IMPLEMENTATION.md` → Integrated into `src/budget.py`

All work described in these documents has been completed and integrated into the current `src/` implementation.

### Deprecated Configs (Root Level)
- `config.*.yaml` variants — Old config examples (use `config.example.yaml` or `config.safe-first-run.yaml`)
- `setup-max-automation.ps1` — Old automation setup (use `setup.bat`/`setup.sh`)
- `first-tweet-config.yaml` — Early minimal config

## Current Documentation

For up-to-date documentation, see:
- **Root README.md** — Main project documentation
- **docs/** — Production documentation suite
  - `observability/` — OpenTelemetry + Jaeger setup, alerting
  - `guides/` — User guides (QUICKSTART, FIRST_TWEET, READ_BUDGET)
  - `telemetry.md` — Telemetry implementation details
  - `REPO_CLEANUP_PROPOSAL.md` — Repository organization plan

## Archive Policy

Files moved to `legacy/` when:
1. **Superseded** — Replaced by better-organized documentation
2. **Milestone complete** — Sprint/phase reports after completion
3. **Deprecated** — Old configuration formats or scripts
4. **Historical value** — Keep for reference but not actively maintained

## Archive Dates
- **November 6, 2025** — Initial legacy planning consolidation
- **November 8, 2025** — Coverage campaign completion; added Sprint 4-5 docs, superseded observability/quickstart files
