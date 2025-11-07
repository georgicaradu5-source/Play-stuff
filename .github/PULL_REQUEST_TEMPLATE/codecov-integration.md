# Codecov integration for Play-stuff

This PR integrates Codecov to monitor and visualize test coverage trends over time. It uploads coverage reports from CI and adds a badge to the README.

- Adds Codecov upload step to `.github/workflows/ci.yml` (Linux, Python 3.12 jobs)
- Documents Codecov badge and usage in README
- No production code changes

Closes #37
