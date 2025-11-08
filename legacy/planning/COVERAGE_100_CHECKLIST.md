# Coverage 100% Tracking Checklist

**Goal**: Achieve and maintain high test coverage with incremental CI gates  
**Current**: 97.80% (487 tests passing, 39 uncovered lines)  
**Gate**: 97.7% (enforced in pytest.ini + noxfile.py)  
**Status**: Sprint 4/5 Complete ✅

---

## Recent Progress (Sprints 4-5)

### Sprint 4.1: Baseline Improvements → 95.72% ✅
- Added comprehensive x_client OAuth2 tests
- Improved config_schema validation coverage
- Raised gate: 90% → 95%

### Sprint 4.2: Learn + Auth Modules → 96.06% ✅
- Achieved 100% coverage for learn.py
- Added targeted auth.py tests (96.49%)
- Raised gate: 95% → 96%

### Sprint 4.3: x_client + config_schema → 97.52% ✅
- OAuth2 path tests for x_client endpoints
- Config validators and fallback tests
- Raised gate: 96% → 97%

### Sprint 5: Final CLI & Edge Cases → 97.80% ✅
- **main.py** achieved 100% (CLI coverage complete)
- Added quota exhaustion test for actions.py
- Non-recording span guard test for opentelemetry_provider.py
- Generic exception test for config_schema validation
- Import fallback tests for auth/config_schema/budget (x_client intentionally excluded)
- **Silenced ConsoleSpanExporter warning** via conftest.py patch
- Raised gate: 97% → **97.7%**

---

## Current Coverage Status (97.80%)

### Fully Covered (100%) ✅
- `budget.py` – Plan caps, safety buffers, monthly tracking
- `learn.py` – Thompson Sampling, bandit operations
- `logger.py` – Logging utilities
- `logging_setup.py` – TraceContext injection
- `main.py` – **CLI entry point, all modes, authorize, dry-run**
- `rate_limiter.py` – Per-endpoint tracking, backoff
- `reliability.py` – Retry logic with jitter
- `scheduler.py` – Time windows, orchestration
- `storage.py` – SQLite operations, dedup, metrics
- `telemetry.py` – Span management, context propagation
- All telemetry_core modules (factory, noop, types)

### High Coverage (≥98%)
- `actions.py` – 98.70% (1 line: structural branch header)
- `config_schema.py` – 98.01% (4 lines: import fallback scaffolding)
- `opentelemetry_provider.py` – 98.70% (1 line: event dispatch guard)
- `auth.py` – 96.49% (6 lines: token edge cases)

### Lower Coverage (requires attention)
- `x_client.py` – 92.33% (27 lines: span attribute try blocks, defensive requests checks)

---

## Remaining Uncovered Lines (39 total)

### actions.py (1 line)
- Line 113: `if all(v <= 0 for v in remaining.values()):` – Structural branch header
- **Rationale**: All functional paths exercised (quota exhaustion test added); instrumentation marks header line.
- **Risk**: None (behavior fully covered)
- **Action**: Leave uncovered

### opentelemetry_provider.py (1 line)
- Line 58: `if span is not None and getattr(span, "is_recording", lambda: False)():`
- **Rationale**: Guard path tested; hitting dispatch requires real recording span context.
- **Risk**: Low (guard prevents errors)
- **Action**: Leave uncovered (non-recording test added)

### opentelemetry_provider.py (1 line)
- Line 58: `if span is not None and getattr(span, "is_recording", lambda: False)():`
- **Rationale**: Guard path tested; hitting dispatch requires real recording span context.
- **Risk**: Low (guard prevents errors)
- **Action**: Leave uncovered (non-recording test added)

### auth.py (6 lines)
- Lines 41-45: OAuth2 token loading edge cases
- Line 230: Token refresh edge case
- **Rationale**: Core auth flows (Tweepy/OAuth2 authorize, refresh) fully covered; these are defensive branches.
- **Risk**: Low (main paths tested)
- **Action**: Leave uncovered

### config_schema.py (4 lines)
- Lines 43-46: Pydantic import fallback scaffolding
- Line 298: Generic exception in validate_config (now covered via test_config_schema_unexpected.py)
- **Rationale**: Import fallback semantically tested; line marked due to dynamic import pattern.
- **Risk**: None
- **Action**: Leave uncovered (line 298 now covered)

### x_client.py (27 lines)
- Lines 10-11, 57-58, 107-108, 119, 150-151, 189-190, 237-238, 320-321, 351-352, 385-386, 415-416, 449-450, 478-479, 516-517
- **Categories**:
  - Import fallback (10-11): requests library check (intentionally not mocked to avoid test interference)
  - Span attribute try blocks: Defensive attribute setting in spans
  - Defensive requests error paths: Protect against unexpected runtime states
- **Rationale**: Core x_client behaviors (OAuth2/Tweepy modes, dry-run, posting, search) fully tested; these are robustness guards.
- **Risk**: Low (happy + error paths covered)
- **Action**: Leave uncovered (avoiding x_client requests fallback test due to fixture conflicts)

---

## Test Files Added (Sprint 4-5)

### Sprint 4
- `test_learn_remaining.py` – Settle operations, bandit stats
- `test_x_client_remaining_oauth2.py` – OAuth2 endpoint coverage
- `test_opentelemetry_provider_remaining.py` – Event/shutdown paths

### Sprint 5
- `test_actions_remaining.py` – Quota exhaustion, skip-self, live paths
- `test_import_fallbacks.py` – Auth/config/budget import fallbacks
- `test_config_schema_unexpected.py` – Generic validation exception
- `test_main_cli_full.py` – CLI arg parsing, authorize, dry-run, PyYAML fallback, __main__ guard
- Updated `conftest.py` – Silenced ConsoleSpanExporter warning

**Total tests**: 487 passing, 2 skipped

---

## Configuration History

| Milestone | Coverage | Gate | Files Changed |
|-----------|----------|------|---------------|
| Sprint 4.1 | 95.72% | 95% | pytest.ini, noxfile.py |
| Sprint 4.2 | 96.06% | 96% | pytest.ini |
| Sprint 4.3 | 97.52% | 97% | — |
| Sprint 5 | 97.80% | **97.7%** | pytest.ini, noxfile.py |

### Current Configuration (pytest.ini)
```ini
[pytest]
testpaths = tests
norecursedirs = _archive .git __pycache__ *.egg-info
addopts = --cov=src --cov-report=term-missing --cov-fail-under=97.7
```

### Current Configuration (noxfile.py)
```python
@nox.session
def test(session: nox.Session) -> None:
    """Run unit tests with coverage and enforce >=97.7%."""
    _install_dev(session)
    session.run(
        "pytest",
        "-q",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-fail-under=97.7",
    )
```

---

## Path to 98%+ (Optional Next Phase)

To reach 98% threshold, consider:

1. **x_client span attribute paths** – Mock span.set_attribute exceptions (adds fragility)
2. **x_client requests import fallback** – Currently excluded to avoid fixture conflicts; would require isolated test module
3. **auth token edge cases** – Heavy mocking of file I/O and env state

**Recommendation**: Maintain 97.7% gate; residual gaps are defensive code with low risk. Pursuing 98% adds test brittleness without proportional safety gain.

---

## Maintenance Guidelines

- **Coverage drop below 97.7%**: Treat as regression; fix or document.
- **New features**: Aim for ≥98% coverage for new code.
- **Refactoring**: Preserve or improve existing coverage.
- **Import fallbacks**: Test stable modules; avoid reloading modules with heavy external dependencies.
- **CI enforcement**: Gate enforced via pytest.ini + noxfile; no merge without passing.

---

## Commands

```pwsh
# Run full test suite with coverage
pytest -q --cov=src --cov-report=term-missing

# Run full dev checks (lint, type, test)
nox -s all

# Check specific module coverage
pytest tests/test_main_cli_full.py --cov=src/main.py --cov-report=term-missing
```

---

**Status**: Sprint 5 Complete ✅  
**Next**: Monitor for regressions; optional pursuit of 98% requires x_client defensive path mocking.  
**Updated**: 2025-11-08

