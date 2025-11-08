# Authentication Requirements by API Endpoint

This document maps X API endpoints to their authentication requirements and access level constraints.

## Summary Table

| Endpoint | Tweepy (OAuth 1.0a) | OAuth2 (PKCE) | Free Tier | Basic Tier | Notes |
|----------|---------------------|---------------|-----------|------------|-------|
| **POST /2/tweets** | ✅ | ✅ | ✅ | ✅ | Posting works with both auth modes |
| **GET /2/users/me** | ✅ | ✅ | ✅ | ✅ | User info works with both |
| **GET /2/users/:id** | ✅ | ✅ | ✅ | ✅ | User lookup works with both |
| **GET /2/tweets/:id** | ✅ | ✅ | ✅ | ✅ | Tweet lookup works with both |
| **POST /2/users/:id/likes** | ✅ | ✅ | ✅ | ✅ | Liking works with both |
| **DELETE /2/users/:id/likes/:tweet_id** | ✅ | ✅ | ✅ | ✅ | Unliking works with both |
| **POST /2/users/:id/retweets** | ✅ | ✅ | ✅ | ✅ | Reposting works with both |
| **DELETE /2/users/:id/retweets/:tweet_id** | ✅ | ✅ | ✅ | ✅ | Unreposting works with both |
| **POST /2/users/:id/following** | ✅ | ✅ | ✅ | ✅ | Following works with both |
| **GET /2/tweets/search/recent** | ✅ | ✅ | ❌ | ✅ | **Requires Basic tier or higher** |
| **POST /1.1/media/upload** | ✅ | ❌ | ✅ | ✅ | **Tweepy ONLY - v1.1 not in OAuth2** |

## Critical Findings

### 🔴 Search Endpoint Limitation (Your Current Issue)
**Endpoint**: `GET /2/tweets/search/recent`
- **Free Tier**: NOT AVAILABLE (causes 401 Unauthorized)
- **Basic Tier**: Available (requires $100/month subscription)
- **Both auth modes support it** - BUT you need Basic tier access

**Your 401 error** is because your X API account is on the **Free tier**, which doesn't include search endpoints.

### 🔴 Media Upload Limitation
**Endpoint**: `POST /1.1/media/upload`
- **Tweepy mode**: ✅ Works (uses OAuth 1.0a which supports v1.1 API)
- **OAuth2 mode**: ❌ Not available (v1.1 endpoints not supported in OAuth 2.0 PKCE)

## Access Tier Matrix

### Free Tier (Your Current Setup)
✅ **Available**:
- Create posts (tweets)
- Reply to posts
- Like/unlike posts
- Repost/unrepost
- Follow/unfollow users
- Get user info
- Get tweet by ID
- Upload media (Tweepy mode only)

❌ **NOT Available**:
- **Search tweets** (search/recent, search/all)
- Advanced filtering
- High volume operations

### Basic Tier ($100/month)
✅ **Everything in Free tier, PLUS**:
- **Tweet search** (search/recent with 7-day lookback)
- Higher rate limits
- More robust for production automation

## Recommended Auth Strategy

### Current Setup: Free Tier
```yaml
# Use Tweepy mode for maximum compatibility
auth_mode: tweepy

# Disable search-dependent features
schedule:
  windows: [morning, afternoon]
cadence:
  weekdays: [1, 2, 3, 4, 5, 6, 7]  # All days for testing
max_per_window:
  post: 1           # ✅ Works on Free tier
  reply: 0          # ❌ Requires search to find tweets
  like: 0           # ❌ Requires search to find tweets
  follow: 0         # ❌ Requires search to find users
  repost: 0         # ❌ Requires search to find tweets
```

### Future: Basic Tier ($100/month)
```yaml
# Can use either mode (Tweepy recommended for media support)
auth_mode: tweepy

# All features enabled
max_per_window:
  post: 1
  reply: 2          # ✅ Search available
  like: 5           # ✅ Search available
  follow: 1         # ✅ Search available
  repost: 0
```

## Implementation Roadmap

### Phase 1: Post-Only Mode (Current - Free Tier)
**Goal**: Validate posting works, build content library

**Config**:
```yaml
auth_mode: tweepy
max_per_window:
  post: 1
  reply: 0
  like: 0
  follow: 0
  repost: 0
```

**Code Changes**: None needed - existing code supports this

### Phase 2: Upgrade to Basic Tier
**Goal**: Enable search-based engagement

**Steps**:
1. Subscribe to Basic tier in X Developer Portal
2. Update config to enable engagement actions
3. Re-run with search queries active

**Config**:
```yaml
auth_mode: tweepy
max_per_window:
  post: 1
  reply: 2
  like: 5
  follow: 1
  repost: 0
```

### Phase 3: Dual Auth Support (Future)
**Goal**: Flexible auth based on operation type

**Strategy**:
- Use **Tweepy** for media upload operations
- Use **OAuth2** for all other v2 endpoints (better token management)
- Client auto-switches based on operation

**Code Changes Needed**:
```python
# In x_client.py - smart auth switching
def create_post(self, text: str, media_ids: list[str] | None = None):
    # If media_ids provided and OAuth2 mode, warn user
    if media_ids and self.auth.mode == "oauth2":
        raise ValueError(
            "Media upload requires Tweepy mode. "
            "Switch to auth_mode: tweepy or use create_post without media."
        )
```

## Testing Matrix

| Feature | Free + Tweepy | Free + OAuth2 | Basic + Tweepy | Basic + OAuth2 |
|---------|---------------|---------------|----------------|----------------|
| Create post | ✅ | ✅ | ✅ | ✅ |
| Upload media | ✅ | ❌ | ✅ | ❌ |
| Search tweets | ❌ | ❌ | ✅ | ✅ |
| Like/reply/follow | ✅* | ✅* | ✅ | ✅ |

\* Posting works, but engagement requires search (not available on Free)

## Immediate Action Items

1. **Update config.yaml** to post-only mode (disable search-dependent actions)
2. **Keep auth_mode: tweepy** for media upload support
3. **Document upgrade path** to Basic tier when ready for full automation
4. **Test post-only workflow** to validate agent works without search

## Conclusion

**Your setup is correct** - the 401 error on search is expected behavior for Free tier accounts. The agent successfully posted using Tweepy mode, which proves authentication is working.

**Next steps**:
1. Run in **post-only mode** to build content
2. Upgrade to **Basic tier** ($100/month) when ready for engagement automation
3. Keep **Tweepy mode** for maximum API compatibility (v1.1 + v2)
