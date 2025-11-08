# Planning & Inspection Notebooks

This project maintains Jupyter notebooks to inspect repository health, validate dry-run behaviors, and track prioritized improvements.

## When to run
- Before major refactors (architecture & coupling checks)
- Before/after release (storage schema, rate limit, and dry-run snapshots)
- When onboarding contributors (show current priorities & validations)

## How to run cleanly
1. Open the notebook in VS Code/Jupyter: `notebooks/Repo_Inspection_and_DryRun.ipynb`
2. Execute cells as needed. For metrics, first generate coverage:
   - Preferred: `nox -s test`
   - Or: `pytest --cov=src --cov-report=xml`
3. Clear outputs before committing:
   ```bash
   jupyter nbconvert --clear-output --inplace notebooks/Repo_Inspection_and_DryRun.ipynb
   ```
4. Keep artifacts lightweight: the notebook writes `*_summary.json` files for downstream use; avoid storing large outputs in the notebook itself.

## Promote checklists to issues
- Copy actionable checklists from the notebook into GitHub Issues.
- Use labels like `improvement`, `telemetry`, `security`, `rate-limit`, `learning`.
- Link back to the notebook cell/section for context.

## Pre-commit setup (outputs cleared)
Choose one of the following to ensure future notebook diffs stay clean:

- nbstripout (simple):
  ```bash
  pip install nbstripout
  nbstripout --install
  ```
- jupyter nbconvert pre-commit hook:
  Add a pre-commit hook that runs:
  ```bash
  jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace notebooks/Repo_Inspection_and_DryRun.ipynb
  ```

For CI, you can also add a check that fails if outputs are present.
