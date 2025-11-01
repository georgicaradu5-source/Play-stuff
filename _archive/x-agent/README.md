# X Agent - Production-Ready Autonomous X (Twitter) Agent

A fully compliant, production-ready autonomous agent for X (Twitter) using **ONLY** the official X API v2. Implements strict budget management, rate limiting, deduplication, and follows X Developer Policy.

## ⚠️ Compliance First

- ✅ Uses only official X API (v2 for posts/interactions, v1.1 for media upload)
- ✅ OAuth 2.0 with PKCE (user context)
- ✅ Respects monthly plan caps (Free/Basic/Pro)
- ✅ Implements per-endpoint rate limiting with backoff/jitter
- ✅ Logs all actions to SQLite
- ✅ Deduplication to prevent repeat content
- ✅ Dry-run mode for safe testing

**Required compliance steps:**
1. Label your X account as "automated" (Settings > Account > Automation)
2. Link to a managing human account in your bio
3. Follow [X Automation Rules](https://help.twitter.com/en/rules-and-policies/twitter-automation) and [Developer Policy](https://developer.twitter.com/en/developer-terms/policy)

## 📊 Plan Caps

X API has **monthly** caps that vary by plan tier:

| Plan | Reads/Month | Writes/Month | Realtime Stream |
|------|-------------|--------------|-----------------|
| **Free** | 100 posts | 500 posts | ❌ |
| **Basic** | 15,000 posts | 50,000 posts | ❌ |
| **Pro** | ~1M posts | ~300K posts | ✅ |

**How X counts:**
- **READS**: Number of posts *returned* by API (not requests). Each post in search results = 1 read.
- **WRITES**: Creates, deletes, likes, retweets, follows, etc.

This agent includes a **budget manager** with:
- Hard stops before exceeding caps
- 5% safety buffer by default
- Real-time usage tracking
- Monthly period reset

## 🚀 Features

### Core Functionality
- ✅ **Create posts** (text + media via v1.1 chunked upload)
- ✅ **Reply** to posts
- ✅ **Like**, **repost** (retweet), **follow** users
- ✅ **Search recent posts** (7-day window with v2 operators)
- ✅ **Fetch user tweets** and profile info
- ✅ **Metrics tracking** (likes, replies, retweets, impressions)

### Safety & Compliance
- ✅ **Budget manager**: Enforces monthly READ/WRITE caps per plan
- ✅ **Rate limiter**: Tracks `x-rate-limit-*` headers, implements exponential backoff with jitter
- ✅ **Deduplication**: SQLite text hashing (7-day window)
- ✅ **Dry-run mode**: Test everything without API calls
- ✅ **Action logging**: Full audit trail in SQLite

### Developer Experience
- ✅ **CLI with argparse**: `--mode`, `--dry-run`, `--safety` flags
- ✅ **YAML config**: Customize queries, topics, limits
- ✅ **OAuth 2.0 PKCE**: Secure authorization with token refresh
- ✅ **Comprehensive logging**: Track every action and rate limit

## 📦 Installation

### Prerequisites
- Python 3.9+
- X Developer account with API credentials ([apply here](https://developer.twitter.com/en/portal/petition/essential/basic-info))

### Setup

#### Windows (PowerShell)
```powershell
# Clone or create project directory
cd x-agent

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
# Edit .env with your X API credentials

# Copy and customize config
copy config.example.yaml config.yaml
# Edit config.yaml with your queries and topics
```

#### Linux/macOS
```bash
cd x-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure
cp .env.example .env
cp config.example.yaml config.yaml
# Edit .env and config.yaml
```

## 🔑 Authentication

### 1. Get X API Credentials
1. Go to [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a project and app (Free tier available)
3. Note your **Client ID** and **Client Secret**
4. Set OAuth 2.0 settings:
   - **Type**: Web App or Native App
   - **Callback URL**: `http://localhost:8080/callback`

### 2. Configure Scopes
Required scopes (set in Developer Portal):
- `tweet.read`, `tweet.write`
- `users.read`
- `offline.access` (for token refresh)
- `like.read`, `like.write`
- `follows.read`, `follows.write`

### 3. Authorize
```bash
# Run OAuth flow (opens browser)
python src/main.py --authorize

# Follow browser prompts to authorize
# Token saved to .token.json
```

## 🎯 Usage

### Quick Start (Dry Run)
Test without making actual API calls:

```bash
python src/main.py --dry-run --mode both
```

### Production Runs

#### Post only
```bash
python src/main.py --mode post --plan free
```

#### Interact only (search, like, reply)
```bash
python src/main.py --mode interact --plan free
```

#### Both (default)
```bash
python src/main.py --mode both --plan free
```

#### Settle metrics for posts
```bash
python src/main.py --mode settle-metrics
```

### Safety Commands

#### Check budget status
```bash
python src/main.py --safety print-budget
```

#### Check rate limits
```bash
python src/main.py --safety print-limits
```

## ⚙️ Configuration

### `config.yaml`

```yaml
plan: free  # free, basic, pro

actions:
  post:
    enabled: true
    max_per_run: 2
    topics:
      - "AI & automation"
      - "developer tools"
  
  interact:
    enabled: true
    max_results_per_query: 5
    queries:
      - query: '(AI OR "artificial intelligence") lang:en -is:retweet -is:reply'
        actions:
          - like
          # - reply
          # - repost
          # - follow
```

### Query Operators (Search Recent)

X API v2 supports powerful operators:

| Operator | Example | Description |
|----------|---------|-------------|
| `lang:` | `lang:en` | Language filter |
| `-is:retweet` | `-is:retweet` | Exclude retweets |
| `-is:reply` | `-is:reply` | Exclude replies |
| `has:images` | `has:images` | Only posts with images |
| `has:videos` | `has:videos` | Only posts with videos |
| `has:links` | `has:links` | Only posts with links |
| `from:` | `from:username` | From specific user |
| `to:` | `to:username` | Mentioning user |
| `#hashtag` | `#AI` | Hashtag search |
| `"phrase"` | `"exact match"` | Exact phrase |
| `OR` | `AI OR ML` | Boolean OR |

**Example queries:**
```yaml
# English AI posts with images, no retweets/replies
'(AI OR "machine learning") lang:en has:images -is:retweet -is:reply'

# Posts from specific users
'(from:user1 OR from:user2) lang:en -is:retweet'

# Topic-based with hashtag
'#Python #Developer -is:retweet -is:reply'
```

**Limits:**
- Free/Basic: 512 chars max per query
- Pro: Longer queries, enhanced operators

## 🏗️ Architecture

```
x-agent/
├── src/
│   ├── auth.py          # OAuth 2.0 PKCE flow
│   ├── x_client.py      # X API v2 client + v1.1 media
│   ├── rate_limiter.py  # Rate limit tracking & backoff
│   ├── budget.py        # Monthly READ/WRITE budget manager
│   ├── storage.py       # SQLite for actions, metrics, usage
│   ├── scheduler.py     # Action orchestrator with jitter
│   └── main.py          # CLI entry point
├── data/
│   └── x_agent.db       # SQLite database (auto-created)
├── .env                 # API credentials (create from .env.example)
├── .token.json          # OAuth tokens (auto-created)
├── config.yaml          # Agent configuration (create from example)
└── requirements.txt     # Python dependencies
```

### Key Components

**1. Budget Manager** (`budget.py`)
- Tracks monthly reads/writes
- Enforces plan-specific caps
- 5% safety buffer (configurable)
- Hard stops before exceeding limits

**2. Rate Limiter** (`rate_limiter.py`)
- Parses `x-rate-limit-*` headers from responses
- Per-endpoint tracking
- Exponential backoff on 429 errors
- Jitter (100ms - 2s) between calls

**3. Storage** (`storage.py`)
- SQLite tables: `actions`, `metrics`, `usage_monthly`, `text_hashes`
- Deduplication via SHA-256 text hashing
- Action audit trail with status
- Metrics history

**4. X Client** (`x_client.py`)
- All v2 endpoints: create, reply, like, repost, follow, search, lookups
- v1.1 media upload: chunked INIT/APPEND/FINALIZE
- Automatic token refresh on 401
- Budget and rate limit integration

**5. Scheduler** (`scheduler.py`)
- Orchestrates post and interact actions
- Random topic/query selection
- Jitter between actions (8-20s)
- Duplicate detection before posting

## 📈 Endpoints Used

### X API v2
| Endpoint | Method | Usage | Counts As |
|----------|--------|-------|-----------|
| `/2/tweets` | POST | Create post | WRITE |
| `/2/tweets/:id` | DELETE | Delete post | WRITE |
| `/2/tweets/:id` | GET | Get tweet | READ (1) |
| `/2/tweets/search/recent` | GET | Search (7-day) | READ (per post) |
| `/2/users/:id/tweets` | GET | User's tweets | READ (per post) |
| `/2/users/:id/likes` | POST | Like post | WRITE |
| `/2/users/:id/retweets` | POST | Repost | WRITE |
| `/2/users/:id/following` | POST | Follow user | WRITE |
| `/2/users/me` | GET | Get auth user | READ (1) |
| `/2/users/by/username/:username` | GET | User lookup | READ (1) |

### X API v1.1
| Endpoint | Method | Usage |
|----------|--------|-------|
| `/1.1/media/upload` | POST | Media upload (INIT/APPEND/FINALIZE) |

## 🛡️ Rate Limits (Per-Endpoint)

Rate limits are **per-endpoint** and tracked via headers:
- `x-rate-limit-limit`: Total requests allowed
- `x-rate-limit-remaining`: Requests left
- `x-rate-limit-reset`: Unix timestamp when resets

**Typical limits (user-context):**
- **Search Recent**: 60 req/15min (Free/Basic), 300 req/15min (Pro)
- **Create Post**: 100 req/15min (varies by tier)
- **Likes/Follows**: Daily limits (~1000/day on paid tiers)

The agent:
1. Checks remaining before each call
2. Waits if below safety threshold (default: 5 remaining)
3. Implements exponential backoff on 429
4. Adds jitter to avoid thundering herd

## 📝 Startup Checklist

Before first production run:

- [ ] X account labeled as "automated" in settings
- [ ] Managing human account linked in bio
- [ ] `.env` configured with valid credentials
- [ ] `config.yaml` customized (queries, topics, limits)
- [ ] OAuth authorization completed (`--authorize`)
- [ ] Tested with `--dry-run` mode
- [ ] Reviewed X Developer Policy and Automation Rules
- [ ] Set correct `--plan` flag (free/basic/pro)

**First live test:**
```bash
# Create one post (safe test)
python src/main.py --mode post --plan free

# Check it worked
python src/main.py --safety print-budget
```

## 🧪 Testing

### Dry Run (Recommended First)
```bash
# Test full flow without API calls
python src/main.py --dry-run --mode both

# Output shows planned actions:
# [DRY RUN] create_post(text='...', ...)
# [DRY RUN] search_recent(query='...', max_results=5)
```

### Live Test (Guarded)
```bash
# Single post test
python src/main.py --mode post --plan free

# Check budget after
python src/main.py --safety print-budget
```

### Smoke Test Script
Create `tests/smoke_test.py`:

```python
from src.storage import Storage
from src.budget import BudgetManager

# Test storage
storage = Storage("data/test.db")
storage.log_action("test", status="success")
print("✓ Storage works")

# Test budget
budget = BudgetManager(storage, plan="free")
budget.print_budget()
print("✓ Budget works")

storage.close()
```

Run: `python tests/smoke_test.py`

## 🔄 Scheduling

### Windows Task Scheduler
```powershell
# Run every 6 hours
schtasks /create /tn "X Agent" /tr "C:\path\to\.venv\Scripts\python.exe C:\path\to\x-agent\src\main.py --mode both --plan free" /sc hourly /mo 6
```

### Linux/macOS cron
```bash
# Edit crontab
crontab -e

# Add line (run every 6 hours)
0 */6 * * * cd /path/to/x-agent && .venv/bin/python src/main.py --mode both --plan free >> logs/agent.log 2>&1
```

## 📊 Monitoring

### Check logs
```bash
# SQLite query: recent actions
sqlite3 data/x_agent.db "SELECT dt, kind, status, post_id FROM actions ORDER BY dt DESC LIMIT 20;"

# Budget status
python src/main.py --safety print-budget

# Rate limit status
python src/main.py --safety print-limits
```

### Metrics dashboard (optional)
Build a simple dashboard by querying `data/x_agent.db`:

```sql
-- Actions by type
SELECT kind, COUNT(*) as count, 
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success
FROM actions 
GROUP BY kind;

-- Monthly usage
SELECT * FROM usage_monthly ORDER BY period DESC;

-- Top posts by likes
SELECT p.post_id, p.text, m.like_count, m.reply_count
FROM actions p
JOIN metrics m ON p.post_id = m.post_id
WHERE p.kind = 'create_post'
ORDER BY m.like_count DESC
LIMIT 10;
```

## 🚨 Troubleshooting

### "Budget exceeded" error
```bash
# Check current usage
python src/main.py --safety print-budget

# Wait for next month or upgrade plan
# Or adjust config.yaml to lower max_per_run
```

### "Rate limited" (429)
```bash
# Check rate limit status
python src/main.py --safety print-limits

# Agent will auto-backoff, but you can:
# 1. Reduce query max_results in config.yaml
# 2. Increase jitter delays
# 3. Run less frequently
```

### "Authorization failed"
```bash
# Re-run OAuth flow
python src/main.py --authorize

# Check .env has correct CLIENT_ID and CLIENT_SECRET
```

### "No posts found" in search
- Check query syntax (use dry-run to debug)
- Verify language codes (en, es, fr, etc.)
- Recent search is 7-day window only
- Try broader queries

## 🔐 Security Best Practices

- ✅ Never commit `.env` or `.token.json`
- ✅ Use environment-specific configs (dev/prod)
- ✅ Rotate tokens periodically
- ✅ Monitor `data/x_agent.db` for suspicious activity
- ✅ Set file permissions: `chmod 600 .env .token.json`
- ✅ Use separate X accounts for dev/prod testing
- ✅ Review action logs regularly

## 🎯 Roadmap

Potential extensions:
- [ ] LLM integration for smart replies (OpenAI, Anthropic)
- [ ] Vector store for semantic dedup (ChromaDB included in deps)
- [ ] Thread detection & conversation tracking
- [ ] Sentiment analysis before engaging
- [ ] Webhook support for real-time triggers
- [ ] Web dashboard for monitoring
- [ ] Multi-account support
- [ ] Advanced scheduling (time-of-day, day-of-week)

## 📚 Resources

- [X API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [X Developer Policy](https://developer.twitter.com/en/developer-terms/policy)
- [X Automation Rules](https://help.twitter.com/en/rules-and-policies/twitter-automation)
- [Rate Limits Reference](https://developer.twitter.com/en/docs/twitter-api/rate-limits)
- [OAuth 2.0 PKCE Flow](https://developer.twitter.com/en/docs/authentication/oauth-2-0/authorization-code)

## 📄 License

MIT License - See LICENSE file for details.

## ⚠️ Disclaimer

This agent is a tool. You are responsible for:
- Complying with X Terms of Service and Developer Policy
- Content posted by the agent
- Staying within your plan's monthly caps
- Monitoring and moderating automated activity

Use responsibly. Start with dry-run mode and low volumes.

---

**Built with ❤️ for compliant X automation**
