# Extensions and Tooling Audit

Recommended tooling for development and operations.

| Category | Tool/Extension | Status | Notes |
| --- | --- | --- | --- |
| Python | ms-python.python | Recommended | Debugging, linting, testing integration |
| Notebooks | ms-toolsai.jupyter | Optional | Run and inspect notebooks in `notebooks/` |
| GitHub | GitHub.vscode-pull-request-github | Optional | Review PRs/issues from VS Code |
| CI | cschleiden.vscode-github-actions | Optional | Monitor Actions runs |
| YAML | redhat.vscode-yaml | Recommended | YAML schema + lint for workflows |
| SQL | ms-mssql.mssql | Optional | Explore SQLite with alt tools; primary is CLI/artifacts |

Dev tools

- Python 3.11+ recommended
- pip + virtualenv/venv
- Optional: nox for local lint/type/test orchestration

Confirm installed vs. missing per developer environment as needed.
