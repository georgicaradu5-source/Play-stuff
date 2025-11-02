# Repository cleanup proposal

Purpose: streamline the root of the repo for a production-ready X Agent by grouping legacy/planning materials under a clearly named folder. This is an advisory plan; no files have been moved yet.

## Proposed new folders

- legacy/planning: historical analyses, sprint notes, and planning notebooks
- legacy/workflows: time-bound automation workflows used only during planning
- docs/guides: keep user-facing quickstart/how-to content

## Candidates to move

- To legacy/planning/
  - AGILE_ANALYSIS.md
  - AGILE_RECOMMENDATIONS.md
  - AUTONOMY_AND_LEARNING_ANALYSIS.md
  - AUTONOMY_RECOMMENDATIONS.md
  - CURRENT_STATE_ANALYSIS.md
  - IMPLEMENTATION_COMPLETE.md
  - IMPLEMENTATION_SUMMARY.md
  - MIGRATION.md
  - NEXT_STEPS.md
  - OBSERVABILITY.md
  - READ_BUDGET_IMPLEMENTATION.md
  - REPOSITORY_ANALYSIS.md
  - SPRINT_2_BACKLOG.md
  - UNIFICATION_PLAN.md
  - notebooks/Sprint_2_Plan.ipynb

- To legacy/workflows/
  - .github/workflows/bootstrap-pr-sprint2.yml

- To docs/guides/ (stay top-level docs but grouped)
  - FIRST_TWEET_GUIDE.md (empty now; optional to drop)
  - FIRST_TWEET_STEPS.md
  - QUICKSTART.md

Notes:

- The existing _archive/ folder remains unchanged as a historical reference.
- docs/telemetry.md stays in docs/.

## Optional renames

- README_READ_BUDGET.md -> docs/guides/READ_BUDGET.md
- READ_BUDGET_IMPLEMENTATION.md -> legacy/planning/READ_BUDGET_IMPLEMENTATION.md

## Git commands (dry-run preview)

The following commands show the intended moves. Run them locally to apply if you approve.

```powershell
# Create targets
mkdir legacy\planning -Force
mkdir legacy\workflows -Force
mkdir docs\guides -Force

# Planning docs
git mv AGILE_ANALYSIS.md legacy/planning/ 2>$null
git mv AGILE_RECOMMENDATIONS.md legacy/planning/ 2>$null
git mv AUTONOMY_AND_LEARNING_ANALYSIS.md legacy/planning/ 2>$null
git mv AUTONOMY_RECOMMENDATIONS.md legacy/planning/ 2>$null
git mv CURRENT_STATE_ANALYSIS.md legacy/planning/ 2>$null
git mv IMPLEMENTATION_COMPLETE.md legacy/planning/ 2>$null
git mv IMPLEMENTATION_SUMMARY.md legacy/planning/ 2>$null
git mv MIGRATION.md legacy/planning/ 2>$null
git mv NEXT_STEPS.md legacy/planning/ 2>$null
git mv OBSERVABILITY.md legacy/planning/ 2>$null
git mv READ_BUDGET_IMPLEMENTATION.md legacy/planning/ 2>$null
git mv REPOSITORY_ANALYSIS.md legacy/planning/ 2>$null
git mv SPRINT_2_BACKLOG.md legacy/planning/ 2>$null
git mv UNIFICATION_PLAN.md legacy/planning/ 2>$null

# Notebook
git mv notebooks/Sprint_2_Plan.ipynb legacy/planning/ 2>$null

# Planning-only workflow
git mv .github/workflows/bootstrap-pr-sprint2.yml legacy/workflows/ 2>$null

# Guides
git mv FIRST_TWEET_GUIDE.md docs/guides/ 2>$null
git mv FIRST_TWEET_STEPS.md docs/guides/ 2>$null
git mv QUICKSTART.md docs/guides/ 2>$null

# Optional read budget rename
if (Test-Path README_READ_BUDGET.md) { git mv README_READ_BUDGET.md docs/guides/READ_BUDGET.md 2>$null }
```

If any listed files are intentionally kept at root, we can mark them with a short note in README and leave them in place.
