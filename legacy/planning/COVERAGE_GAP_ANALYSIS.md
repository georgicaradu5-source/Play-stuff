# Coverage Gap Analysis & 100% Roadmap

**Current Status**: 82.21% coverage (201 tests, 1776 statements, 316 missed)  
**Target**: 100% coverage with incremental CI gates  
**Generated**: November 7, 2025

---

## Coverage Breakdown by Module

### 🎯 Priority 1: Telemetry Core (38 uncovered lines → Target: 100%)

#### `src/telemetry_core/providers/opentelemetry_provider.py` - 62.34% (29 missed)
**Lines**: 58, 73-75, 80-81, 85-92, 96-101, 104-107, 110-115

**Gaps**:
- `shutdown()` method exception handling (lines 73-75)
- OTLP exporter configuration edge cases (80-81, 85-92)
- Console exporter fallback paths (96-101)
- Provider context manager cleanup (104-107)
- Resource attribute edge cases (110-115)
- TracerProvider initialization failures (58)

**Tests needed**:
- [ ] Test shutdown() when provider.shutdown() raises
- [ ] Test OTLP endpoint with invalid URL format
- [ ] Test console exporter with stdout closed
- [ ] Test resource attribute validation
- [ ] Test TracerProvider with invalid service name

#### `src/telemetry_core/noop.py` - 63.33% (11 missed)
**Lines**: 11, 14, 17, 20, 25, 28, 34, 37, 40, 43, 46

**Gaps**: All no-op stub methods (low value but needed for 100%)
- NoopTelemetry context manager methods
- NoopSpan attribute setters
- NoopTimer context manager

**Tests needed**:
- [ ] Test NoopTelemetry.start_span() returns NoopSpan
- [ ] Test NoopSpan.set_attribute() no-ops
- [ ] Test NoopSpan.add_event() no-ops
- [ ] Test NoopSpan.set_status() no-ops
- [ ] Test NoopTelemetry.start_timer() returns NoopTimer
- [ ] Test NoopTimer.__enter__/__exit__ no-ops

#### `src/telemetry.py` - 71.76% (24 missed)
**Lines**: 52, 66-76, 88-90, 119, 132, 139, 142, 145, 148, 151, 154, 168-177

**Gaps**:
- Context manager paths (`__enter__`, `__exit__`)
- Timer decorator edge cases
- Span attribute validation
- Error handling in telemetry init

**Tests needed**:
- [ ] Test Telemetry as context manager (with/as)
- [ ] Test timer decorator with exceptions
- [ ] Test span set_attribute with invalid types
- [ ] Test telemetry disabled via env var
- [ ] Test add_event with large payloads

#### `src/telemetry_core/factory.py` - 90.48% (2 missed)
**Lines**: 26, 40

**Gaps**:
- ImportError fallback when OpenTelemetry not installed
- Factory method error handling

**Tests needed**:
- [ ] Test create_telemetry() when OpenTelemetry import fails
- [ ] Test noop fallback on factory error

---

### 🎯 Priority 2: x_client Retry/Error Loops (98 uncovered → Target: 100%)

#### `src/x_client.py` - 72.16% (98 missed)
**Lines**: 10-11, 39, 57-58, 63-98, 107-108, 114-128, 131, 150-151, 158-164, 167, 189-190, 192-193, 210, 237-238, 278, 291, 320-321, 327-329, 332, 351-352, 354-355, 363, 385-386, 388-389, 397, 400, 415-416, 418-419, 427, 430, 449-450, 452-453, 461, 464, 478-479, 481-482, 489-503, 516-517, 519-520

**Gaps** (grouped by method):
- **Imports/Init** (10-11): Module import fallbacks
- **from_env()** (39, 57-58, 63-98): OAuth2 token loading errors, env validation
- **get_me()** (107-108, 114-128): Tweepy error paths, OAuth2 failures
- **get_user_by_username()** (150-151, 158-164): 404 handling, retry exhaustion
- **create_post()** (189-190, 192-193, 210): Media validation, quote tweet errors
- **delete_post()** (237-238): Tweepy/OAuth2 error branches
- **search_recent()** (278, 291): Pagination errors, empty results
- **like_post()** (320-321, 327-329): Retry logic, me_id failures
- **unlike_post()** (351-352, 354-355): Similar to like_post
- **retweet()** (385-386, 388-389): Retry logic, Tweepy errors
- **unretweet()** (415-416, 418-419): Similar to retweet
- **follow_user()** (449-450, 452-453): Retry logic, OAuth2/Tweepy divergence
- **get_tweet()** (478-479, 481-482): 404 handling, retry exhaustion
- **upload_media()** (489-503): File validation, v1.1 API errors
- **_oauth2_request()** (516-517, 519-520): Generic HTTP error paths

**Tests needed**:
- [ ] Test get_me() with expired token (401)
- [ ] Test get_user_by_username() with network timeout
- [ ] Test create_post() with invalid media IDs
- [ ] Test delete_post() 403 forbidden
- [ ] Test search_recent() with malformed query
- [ ] Test like_post() retry on 429 (rate limit)
- [ ] Test unlike_post() on already-unliked tweet
- [ ] Test retweet() 403 (already retweeted)
- [ ] Test unretweet() on non-retweeted tweet
- [ ] Test follow_user() 403 (protected account)
- [ ] Test get_tweet() 404 (deleted tweet)
- [ ] Test upload_media() with invalid file path
- [ ] Test upload_media() file too large
- [ ] Test _oauth2_request() with 500 exhausting retries

---

### 🎯 Priority 3: CLI & Entry Points (6 uncovered → Target: 100%)

#### `src/main.py` - 96.47% (6 missed)
**Lines**: 13-14, 245-247, 345

**Gaps**:
- Import fallbacks (13-14): yaml/pydantic missing
- BudgetManager import in settle path (245-247)
- Final `if __name__ == "__main__"` guard (345)

**Tests needed**:
- [ ] Test main with PyYAML not installed
- [ ] Test main with config_schema not installed
- [ ] Test settle operation when BudgetManager import fails
- [ ] Test direct execution via `python src/main.py`

---

### 🎯 Priority 4: Rate Limiter & Reliability (19 uncovered → Target: 100%)

#### `src/rate_limiter.py` - 78.05% (18 missed)
**Lines**: 55, 67, 114, 118, 122-137

**Gaps**:
- Sleep override in wait calculations (55, 67)
- Per-endpoint rate limit math (114, 118)
- Reset time edge cases (122-137)

**Tests needed**:
- [ ] Test wait_if_needed() with custom sleep function
- [ ] Test rate limit with reset time in past
- [ ] Test concurrent requests hitting same endpoint limit
- [ ] Test print_limits() output formatting

#### `src/reliability.py` - 97.87% (1 missed)
**Line**: 98

**Gap**: `resp.raise_for_status()` after retry exhaustion fallback

**Tests needed**:
- [ ] Test non-retryable error after all retries exhausted (edge case)

---

### 🎯 Priority 5: Supporting Modules (99 uncovered → Target: 100%)

#### `src/actions.py` - 84.42% (12 missed)
**Lines**: 64, 98, 113, 121-123, 132-133, 142-143, 152-153

**Gaps**: Error handling in post/interact actions

**Tests needed**:
- [ ] Test run_post_action() with empty topics
- [ ] Test run_interact_action() with search failure
- [ ] Test dedupe logic with similar texts

#### `src/auth.py` - 73.68% (45 missed)
**Lines**: 19-20, 26-27, 39-48, 51, 130, 148-166, 177, 206-230, 245-247, 269, 280-282

**Gaps**: OAuth 1.0a/2.0 flow edge cases, token refresh, credential validation

**Tests needed**:
- [ ] Test OAuth 1.0a with invalid credentials
- [ ] Test OAuth 2.0 token refresh with expired token
- [ ] Test authorize_oauth2() user denial flow
- [ ] Test from_env() with missing env vars

#### `src/budget.py` - 70.79% (26 missed)
**Lines**: 10-11, 80-81, 107, 120, 125, 133, 140, 144-152, 183-186, 195-198, 207-208

**Gaps**: Plan cap calculations, storage usage, monthly reset

**Tests needed**:
- [ ] Test plan caps for free/basic/pro tiers
- [ ] Test monthly reset logic
- [ ] Test storage usage exceeding limits
- [ ] Test can_post() when at monthly cap

#### `src/scheduler.py` - 88.52% (14 missed)
**Lines**: 80-81, 91-92, 173-174, 184, 189-190, 220-221, 223-224, 238

**Gaps**: Weekend/holiday logic, window selection, topic selection

**Tests needed**:
- [ ] Test run_scheduler() on weekends (no posting)
- [ ] Test window selection with no available windows
- [ ] Test topic selection with empty topics list
- [ ] Test both mode (post + interact)

#### `src/storage.py` - 99.32% (1 missed)
**Line**: 360

**Gap**: Single edge case in bandit update logic

**Tests needed**:
- [ ] Test bandit_update() with edge case on line 360

#### `src/config_schema.py` - 90.05% (20 missed)
**Lines**: 24-48, 298, 303, 312, 358, 378-379

**Gaps**: Pydantic model __init__, validation edge cases

**Tests needed**:
- [ ] Test Config model with invalid auth_mode
- [ ] Test Config model with invalid plan
- [ ] Test Config validation with malformed schedule

#### `src/learn.py` - 90.16% (6 missed)
**Lines**: 95, 103-105, 115-116

**Gaps**: Thompson Sampling edge cases, print output

**Tests needed**:
- [ ] Test select_arm() with no prior data
- [ ] Test settle() with missing metrics
- [ ] Test print_bandit_stats() output

#### `src/logging_setup.py` - 90.00% (3 missed)
**Lines**: 44-47

**Gap**: TraceContext injection edge case

**Tests needed**:
- [ ] Test attach_tracecontext_to_logs() with no active span

---

## Incremental Gate Roadmap

### Phase 1: Telemetry Core (Target: 85%)
- Complete telemetry_core/noop.py → 100%
- Complete telemetry_core/providers/opentelemetry_provider.py → 100%
- Complete telemetry.py → 100%
- Complete telemetry_core/factory.py → 100%
- **Raise gate**: 75% → 85%

### Phase 2: x_client Retry Loops (Target: 92%)
- Add 14 x_client retry/error tests
- Cover all engagement method error paths
- Cover search/pagination edge cases
- **Raise gate**: 85% → 92%

### Phase 3: CLI & Supporting (Target: 98%)
- Complete main.py → 100%
- Complete rate_limiter.py → 100%
- Complete reliability.py → 100%
- Complete actions.py → 100%
- **Raise gate**: 92% → 98%

### Phase 4: Final Push (Target: 100%)
- Complete auth.py → 100%
- Complete budget.py → 100%
- Complete scheduler.py → 100%
- Complete storage.py → 100%
- Complete config_schema.py → 100%
- Complete learn.py → 100%
- Complete logging_setup.py → 100%
- **Raise gate**: 98% → 100%

---

## Test File Additions Needed

1. `tests/test_telemetry_noop.py` (extend existing with 6 tests)
2. `tests/test_telemetry_provider_advanced.py` (10 tests for shutdown/edge cases)
3. `tests/test_telemetry_context_managers.py` (8 tests)
4. `tests/test_x_client_retry_loops.py` (14 tests for error paths)
5. `tests/test_x_client_oauth2_edge_cases.py` (12 tests)
6. `tests/test_main_imports.py` (4 tests for import fallbacks)
7. `tests/test_rate_limiter_advanced.py` (6 tests for edge cases)
8. `tests/test_actions_edge_cases.py` (8 tests)
9. `tests/test_auth_oauth_flows.py` (15 tests)
10. `tests/test_budget_caps.py` (10 tests)
11. `tests/test_scheduler_windows.py` (extend existing with 6 tests)
12. `tests/test_config_validation.py` (extend existing with 8 tests)

**Total new tests estimated**: ~97 tests (bringing total from 201 to ~298)

---

## Success Metrics

- ✅ All 1776 statements covered
- ✅ CI gate at 100% (enforced)
- ✅ Test suite runs in < 30 seconds
- ✅ HTML coverage report shows all green
- ✅ Documentation updated (README, CONTRIBUTING)

---

## Next Action

Start with **Phase 1: Telemetry Core** to push from 82.21% to 85% by completing:
1. `tests/test_telemetry_noop.py` extension (6 tests)
2. `tests/test_telemetry_provider_advanced.py` (10 tests)
3. `tests/test_telemetry_context_managers.py` (8 tests)

This will cover 38 uncovered lines and validate the incremental approach before tackling larger modules.
