# Documentation Index

Welcome to the X Agent Unified documentation hub. This index highlights key resources for architecture, operations, and ongoing improvement.

## Core References
- **Main README**: Project overview, architecture, setup – see `../README.md`
- **Quick Start Guide**: Step-by-step setup – `guides/QUICKSTART.md`
- **Production Readiness**: Operational & quality gates – `PRODUCTION_READINESS.md`
- **Environments & Secrets**: GitHub environments and secret management – `ENVIRONMENTS.md`
- **Telemetry**: Enabling and using traces – `telemetry.md`

## Notebooks & Roadmap
- **Strategic Inspection Notebook**: `notebooks/Repo_Inspection_and_DryRun.ipynb` – latest repo inspection, prioritized improvements, dry-run validation, coverage snapshot (run `nox -s test` or `pytest --cov=src --cov-report=xml` first for coverage).
- **Notebook Operations Guide**: `observability/notebooks.md` – when to run, clearing outputs, promoting checklists.
- **Improvements Roadmap**: `roadmap/IMPROVEMENTS.md` – mirrored modularization, telemetry, rate limit, security, learning loop checklists.

## Planning & Risk
- **Risk Register**: `RISK_REGISTER.md`
- **Opportunities / Backlog**: `OPPORTUNITIES.md`
- **Sprints Summary**: `SPRINTS.md`

## Operations & Support
- **Troubleshooting 403**: `TROUBLESHOOTING_403.md`
- **Assistance Checklist**: `ASSISTANCE_CHECKLIST.md`
- **Extensions Audit**: `EXTENSIONS_AUDIT.md`

## Contributing
- Use the inspection notebook to find the current priorities.
- Convert checklist items into GitHub Issues (labels: `improvement`, component labels like `telemetry`, `security`, `rate-limit`, `learning`).
- Keep notebooks clean: outputs are auto-stripped via pre-commit (nbstripout).

## Quick Validation Commands
```bash
nox -s all
python src/main.py --dry-run --mode both
python scripts/peek_actions.py --limit 10
```

If you add new docs, reference them here to keep discovery simple.
