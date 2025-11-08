# Modularization Inventory: Issue #38

## Current Architecture Analysis

### src/x_client.py (533 lines)
**Purpose:** Unified X API client with dual auth support (Tweepy + OAuth2)

**Current Responsibilities:**
1. **API Communication Layer**
   - HTTP request handling (`request_with_retries` integration)
   - Auth header management (mode-specific: Tweepy vs OAuth2)
   - Endpoint routing (v2 API, v1.1 media upload)
   
2. **User Operations**
   - `get_me()` - Get authenticated user info
   - `get_user_by_username()` - Lookup user by username
   
3. **Post Operations**
   - `create_post()` - Create tweet with optional media
   - `delete_post()` - Delete a tweet
   - `get_tweet()` - Retrieve single tweet
   - `get_user_tweets()` - Retrieve user's timeline
   
4. **Engagement Operations**
   - `like_post()` - Like a tweet
   - `unlike_post()` - Remove like
   - `repost()` - Retweet
   - `unrepost()` - Remove retweet
   
5. **Social Operations**
   - `follow_user()` - Follow account
   - `unfollow_user()` - Unfollow account
   
6. **Search Operations**
   - `search_recent()` - Search tweets (requires Basic+ tier)
   
7. **Media Operations** (Tweepy only)
   - `upload_media()` - Upload media file
   - `_upload_init()`, `_upload_append()`, `_upload_finalize()` - Chunked upload helpers
   - `_get_media_type()` - Determine MIME type

**Tightly Coupled Elements:**
- Auth mode switching logic embedded throughout
- Direct dependency on `UnifiedAuth` class
- Rate limiter integration (via reliability module)
- Telemetry span creation mixed with business logic
- Dry-run behavior scattered across methods

---

### src/actions.py (158 lines)
**Purpose:** Template-based content generation and interaction orchestration

**Current Responsibilities:**
1. **Content Generation**
   - `TEMPLATES` - Topic-based post templates
   - `REPLY_TEMPLATES` - Reply text templates
   - `choose_template()` - Random template selection
   - `make_post()` - Generate post text + optional media
   - `helpful_reply()` - Generate reply text
   
2. **Search-Based Actions**
   - `act_on_search()` - Orchestrate reply/like/follow from search results
     - Filters out self-posts
     - Applies per-action limits
     - Deduplicates via storage
     - Adds jitter between actions
   
3. **Post-Based Actions**
   - `act_on_posts()` - Like/repost from user timeline
     - Similar orchestration to search actions
     - Filters out already-engaged posts

**Tightly Coupled Elements:**
- Direct `XClient` dependency (type hint + method calls)
- Direct `Storage` dependency for deduplication
- Mixing of business logic (template selection) with orchestration (action loops)
- Hardcoded jitter/sleep logic
- No separation between content strategy and execution

---

## Proposed Modular Structure

### New Module: src/api/
**Responsibility:** Pure API communication layer

**Components:**
- `api/client.py` - Low-level HTTP client (auth-agnostic)
  - Request/response handling
  - Endpoint URL construction
  - Error handling + retries
  
- `api/endpoints.py` - API endpoint definitions
  - User endpoints
  - Post endpoints
  - Engagement endpoints
  - Search endpoints
  - Media endpoints
  
- `api/models.py` - Data models (optional, if we add Pydantic)
  - Request models
  - Response models
  
**Benefits:**
- Testable in isolation (mock HTTP)
- Auth logic stays separate
- Clear API contract

---

### New Module: src/business/
**Responsibility:** Business logic without orchestration

**Components:**
- `business/content.py` - Content generation
  - Template management
  - Post composition
  - Reply generation
  
- `business/filters.py` - Action filters
  - Self-post filter
  - Deduplication logic
  - Eligibility rules
  
- `business/limits.py` - Limit enforcement
  - Per-action counters
  - Backoff calculation
  
**Benefits:**
- Reusable across different orchestration scenarios
- Easier to unit test (no API calls needed)
- Clear separation of "what" from "how"

---

### New Module: src/orchestration/
**Responsibility:** Coordinate API calls + business logic

**Components:**
- `orchestration/search_actions.py` - Search-based workflows
  - Replaces `act_on_search()`
  - Composes: search → filter → act → log
  
- `orchestration/post_actions.py` - Timeline-based workflows
  - Replaces `act_on_posts()`
  
- `orchestration/workflows.py` - Common workflow patterns
  - Retry logic
  - Jitter/throttle
  - Telemetry wrapping
  
**Benefits:**
- High-level workflows separated from low-level API
- Easier to add new workflows (e.g., scheduled posting)
- Testable with mock API + business layers

---

### Refactored: src/x_client.py
**New Responsibility:** Facade over API layer + auth integration

**Kept Methods (delegating to `src/api/`):**
- User operations (get_me, get_user_by_username)
- Post operations (create_post, delete_post, get_tweet)
- Engagement (like, unlike, repost, unrepost)
- Social (follow, unfollow)
- Search (search_recent)
- Media (upload_media - Tweepy only)

**Removed Complexity:**
- Internal HTTP logic → moved to `api/client.py`
- Endpoint URLs → moved to `api/endpoints.py`
- Auth header construction → stays in `UnifiedAuth`, called by `api/client.py`

**Benefits:**
- Smaller, focused class
- Easier to mock in tests
- Clear dependency injection points

---

### Refactored: src/actions.py
**New Responsibility:** Entry point for orchestration (or deprecated)

**Options:**
1. **Keep as facade:** Delegate to `orchestration/` modules
2. **Deprecate:** Move all logic to `orchestration/`, update `main.py` imports

**Recommendation:** Option 2 (deprecate)
- Avoids redundant indirection
- Forces clear imports in `main.py`
- Signals to contributors: "orchestration is the new pattern"

---

## Migration Strategy

### Phase 1: Extract API Layer (Non-Breaking)
1. Create `src/api/client.py` with HTTP logic from `x_client.py`
2. Create `src/api/endpoints.py` with URL constants
3. Update `x_client.py` to delegate to `api/client.py` (keep existing interface)
4. Add tests for `api/client.py` (mock requests)
5. Verify: `pytest tests/test_x_client*.py -v` still passes

### Phase 2: Extract Business Logic (Non-Breaking)
1. Create `src/business/content.py` with templates and generators from `actions.py`
2. Create `src/business/filters.py` with dedup/self-check logic
3. Update `actions.py` to import from `business/` (keep existing interface)
4. Add tests for `business/` modules
5. Verify: `pytest tests/test_actions*.py -v` still passes

### Phase 3: Extract Orchestration (Breaking - Requires Main Update)
1. Create `src/orchestration/search_actions.py` with refactored `act_on_search()`
2. Create `src/orchestration/post_actions.py` with refactored `act_on_posts()`
3. Update `main.py` to import from `orchestration/` instead of `actions.py`
4. Add tests for `orchestration/` modules
5. Verify: End-to-end dry-run works

### Phase 4: Cleanup
1. Remove now-empty functions from `actions.py` (or delete file)
2. Update all imports in tests
3. Update documentation (README, docs index)
4. Run full validation suite

---

## Test Coverage Plan

### New Test Files:
- `tests/test_api_client.py` - HTTP layer tests (mock requests)
- `tests/test_api_endpoints.py` - URL construction tests
- `tests/test_business_content.py` - Template/generation tests
- `tests/test_business_filters.py` - Filter logic tests
- `tests/test_orchestration_search.py` - Search workflow tests
- `tests/test_orchestration_post.py` - Post workflow tests

### Updated Test Files:
- `tests/test_x_client*.py` - Now test facade behavior
- `tests/test_actions*.py` - Migrate to orchestration tests

### Coverage Target: ≥97% (current baseline)

---

## Acceptance Criteria (from Execution Plan)

- [x] Inventory complete
- [ ] Module structure designed
- [ ] Extraction implemented (non-breaking phases)
- [ ] Tests added/expanded for new modules
- [ ] Main.py updated to use orchestration layer
- [ ] Documentation updated (README, docs index)
- [ ] Validation: `make all`, `make check-notebooks`, `pre-commit run --all-files`
- [ ] Coverage ≥97%
- [ ] Both auth modes work
- [ ] Dry-run remains non-posting
- [ ] PR links to roadmap and milestone

---

## Open Questions

1. **Pydantic models?** Add `api/models.py` with typed requests/responses?
   - Pro: Type safety, validation
   - Con: Extra dependency, migration effort
   - Decision: Defer to future issue (not blocking)

2. **Keep actions.py as facade?** Or deprecate entirely?
   - Decision: Deprecate (clearer import path)

3. **Auth integration point?** Should `api/client.py` take `UnifiedAuth` or just headers?
   - Decision: Take `UnifiedAuth` (preserves mode-switching logic)

4. **Telemetry spans?** Keep in orchestration or also add to API layer?
   - Decision: Both (API spans for low-level, orchestration spans for workflows)

---

*Next Step: Begin Phase 1 (Extract API Layer)*
