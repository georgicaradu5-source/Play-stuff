# Issue Execution Plan: Strategic Enhancements v1.2.0

This document outlines the recommended execution sequence for milestone issues #38–#42, including branching strategy, validation steps, and acceptance criteria.

## Execution Sequence

Issues should be tackled in dependency order to maximize parallelization and minimize rework:

```
#38 (Modularization) → #39 (Telemetry) → #40 (Rate Limiter) → #41 (Security) → #42 (Learning Loop)
                    ↘                  ↘                      ↘
                      Can parallelize after #38 is merged
```

## Pre-Work Checklist (All Issues)

Before starting any issue:
- [ ] Ensure `main` branch is up-to-date: `git pull origin main`
- [ ] Verify tests pass: `pytest -v` or `make test`
- [ ] Check notebook hygiene: `make check-notebooks`
- [ ] Run pre-commit: `pre-commit run --all-files`

## Issue #38: Modularization

**Goal:** Decouple `src/x_client.py` and `src/actions.py` to separate API, business logic, and orchestration concerns.

**Branch:** `feature/modularization`

**Steps:**
1. **Inventory:** Audit `src/x_client.py` and `src/actions.py` for tightly coupled logic
2. **Extract:** Create new modules (e.g., `src/api/`, `src/orchestration/`)
3. **Refactor:** Move logic to appropriate modules while preserving interfaces
4. **Test:** Add/expand unit tests for new modules (`tests/test_api_*.py`, `tests/test_orchestration_*.py`)
5. **Validate:**
   ```bash
   make all  # lint + type + test
   make check-notebooks
   pre-commit run --all-files
   pytest -v --cov=src --cov-report=term
   ```
6. **Docs:** Update `README.md` and `docs/` to reflect new module boundaries

**Acceptance:**
- All checklist items in `docs/roadmap/IMPROVEMENTS.md` (Modularization section) completed or deferred with rationale
- Test coverage maintained at ≥97%
- Both Tweepy and OAuth2 modes work
- Dry-run (`--dry-run`) remains non-posting
- PR links to roadmap section and milestone

**PR Template:**
```markdown
Closes #38

## Summary
Refactored x_client and actions into modular structure per roadmap.

## Changes
- Created `src/api/` for API interactions
- Created `src/orchestration/` for business logic
- Updated tests in `tests/test_api_*.py` and `tests/test_orchestration_*.py`

## Validation
- [x] `make all` passes
- [x] `make check-notebooks` passes
- [x] Coverage ≥97%
- [x] Dry-run tested in both auth modes

## Roadmap
See [Modularization section](../docs/roadmap/IMPROVEMENTS.md#modularization)
```

---

## Issue #39: Telemetry Expansion

**Depends on:** #38 (recommended, not blocking)

**Goal:** Add granular tracing spans and log context propagation.

**Branch:** `feature/telemetry-expansion`

**Steps:**
1. **Audit:** Review current tracing coverage using `telemetry.start_span` calls
2. **Add Spans:** Instrument auth, post, like, rate limiter, storage with spans
3. **Context Injection:** Ensure W3C TraceContext propagates to logs via `logging_setup.py`
4. **Validate:** Enable telemetry (`$env:ENABLE_TELEMETRY='true'`) and verify spans in OTLP endpoint
5. **Test:**
   ```bash
   pytest tests/test_telemetry*.py -v
   make all
   ```
6. **Docs:** Update `docs/telemetry.md` with new span examples

**Acceptance:**
- Roadmap checklist completed
- Tests cover span creation in both auth modes
- Telemetry remains optional (no-op fallback works)
- Rate limiter + dry-run preserved

---

## Issue #40: Rate Limiter Integration

**Depends on:** #39 (recommended)

**Goal:** Route all client actions through rate limiter with pre/post checks and logging.

**Branch:** `feature/rate-limiter-integration`

**Steps:**
1. **Route Actions:** Update `src/x_client.py` to enforce rate limit checks before all API calls
2. **Logging:** Add backoff/jitter decision logging via `storage.log_action`
3. **Tests:** Expand `tests/test_rate_limiter_*.py` for burst traffic and 429 recovery
4. **Validate:**
   ```bash
   pytest tests/test_rate_limiter*.py -v
   make all
   ```
5. **Docs:** Document integration contract in `docs/README.md`

**Acceptance:**
- All actions (post/like/follow/search) go through rate limiter
- Backoff/jitter logged with telemetry spans
- Tests for burst scenarios and 429 handling
- Dry-run safety intact

---

## Issue #41: Security Hardening

**Depends on:** #40 (recommended)

**Goal:** Audit token handling, prevent sensitive data in logs, harden API boundaries.

**Branch:** `feature/security-hardening`

**Steps:**
1. **Token Audit:** Review `.env`, `src/auth.py`, `src/storage.py` for token storage/rotation
2. **Log Redaction:** Ensure no tokens/secrets in logs or exceptions (check `logger.py`, `logging_setup.py`)
3. **Input Validation:** Harden external API boundaries (user input, config schema)
4. **Red Team Tests:** Add security-focused tests (`tests/test_security_*.py`)
5. **Validate:**
   ```bash
   pytest tests/test_security*.py -v
   make all
   grep -r "Bearer\|api_key\|token" src/ tests/ --exclude-dir=__pycache__
   ```
6. **Docs:** Add security section to `docs/PRODUCTION_READINESS.md`

**Acceptance:**
- Secrets rotation policy documented
- Logs/exceptions redact sensitive data
- Input validation added/expanded
- Security tests pass

---

## Issue #42: Learning Loop Refinement

**Depends on:** #41 (recommended)

**Goal:** Tune Thompson Sampling parameters, expand metrics, simulate edge cases.

**Branch:** `feature/learning-loop-refinement`

**Steps:**
1. **Parameter Tuning:** Review and adjust Thompson Sampling priors in `src/learn.py`
2. **Metrics Expansion:** Add logging for exploration/exploitation balance
3. **Simulation:** Add tests for varied scenarios (`tests/test_learn_*.py`)
4. **Validate:**
   ```bash
   pytest tests/test_learn*.py -v
   make all
   ```
5. **Docs:** Document new config keys in README TL;DR and `config.example.yaml`

**Acceptance:**
- Thompson Sampling improvements don't regress existing metrics
- Tests for exploration/exploitation balance
- Simulation tests for edge cases
- Before/after metrics summary in PR

---

## Post-Issue Checklist

After merging each issue:
- [ ] Update milestone progress: `python scripts/update_milestone_status.py --milestone 2 --status-file docs/roadmap/STATUS.md`
- [ ] Check GitHub Actions for workflow success
- [ ] Verify `docs/roadmap/STATUS.md` reflects closed issue
- [ ] Celebrate progress! 🎉

---

## Validation Commands Reference

```bash
# Full quality gate
make all

# Individual checks
make lint
make type
make test

# Notebook hygiene
make check-notebooks

# Pre-commit hooks
pre-commit run --all-files

# Coverage report
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=xml

# Dry-run validation
python src/main.py --mode both --dry-run true
```

---

## Milestone Status

Track overall progress at: [docs/roadmap/STATUS.md](STATUS.md)

Auto-updated daily by GitHub Actions workflow: `.github/workflows/milestone-progress.yml`
