# X Agent - Unified Production-Ready Autonomous X (Twitter) Agent

A fully unified, production-ready autonomous agent for X (Twitter) that combines the best features from both implementations. Supports **both OAuth 1.0a (Tweepy) and OAuth 2.0 PKCE** authentication methods.

## 🎯 Unified Features

### From Both Implementations
- ✅ **Dual Auth Support**: Choose between Tweepy (OAuth 1.0a) or OAuth 2.0 PKCE
- ✅ **Thompson Sampling Learning**: Optimizes topic/time-window choices based on engagement
- ✅ **Comprehensive Budget Manager**: Free/Basic/Pro plan support with monthly caps
- ✅ **Advanced Rate Limiting**: Per-endpoint tracking, exponential backoff, jitter
- ✅ **Time-Window Scheduling**: Morning/afternoon/evening optimal posting times
- ✅ **Template-Based Content**: Organized by topics with variation
- ✅ **Full Compliance**: Respects X Developer Policy and Automation Rules
- ✅ **SQLite Storage**: Actions, metrics, usage tracking, deduplication
- ✅ **Dry-Run Mode**: Safe testing without API calls

## 📦 Quick Start

### Installation
```powershell
# Windows
.\setup.bat

# Linux/macOS
chmod +x setup.sh && ./setup.sh
```

### Choose Your Auth Method

#### Option 1: Tweepy (OAuth 1.0a) - Simpler Setup
```bash
# Edit .env with OAuth 1.0a credentials
X_AUTH_MODE=tweepy
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
```

#### Option 2: OAuth 2.0 PKCE - Modern, Recommended
```bash
# Edit .env with OAuth 2.0 credentials
X_AUTH_MODE=oauth2
X_CLIENT_ID=your_client_id
X_CLIENT_SECRET=your_client_secret

# Run authorization flow
python src/main.py --authorize
```

### Test and Run
```bash
# Test (dry-run)
python src/main.py --dry-run --mode both

# Go live
python src/main.py --mode both --plan free
```

## 🏗️ Architecture

```
x-agent-unified/
├── src/
│   ├── auth.py              # Dual auth: Tweepy + OAuth 2.0 PKCE
│   ├── x_client.py          # Unified X API client
│   ├── budget.py            # Budget manager with plan tiers
│   ├── rate_limiter.py      # Rate limit guard
│   ├── storage.py           # SQLite storage
│   ├── scheduler.py         # Time-window scheduler
│   ├── actions.py           # Template-based actions
│   ├── learn.py             # Thompson Sampling learning
│   └── main.py              # CLI entry point
├── config.yaml              # Configuration
├── .env                     # Credentials
└── README.md
```

## 🔑 Authentication Comparison

| Feature | Tweepy (OAuth 1.0a) | OAuth 2.0 PKCE |
|---------|---------------------|----------------|
| Setup | Simpler, 4 tokens | Requires auth flow |
| Scopes | Fixed | Granular control |
| Token Refresh | Manual | Automatic |
| Best For | Quick start, personal | Production, apps |

## ⚙️ Configuration

```yaml
# Auth mode
auth_mode: tweepy  # or oauth2

# Plan tier
plan: free  # free, basic, pro

# Topics for content
topics:
  - power-platform
  - data-viz
  - automation

# Queries for interaction
queries:
  - query: '(Power BI OR "Power Platform") lang:en -is:retweet -is:reply'
    actions: [like, reply]

# Time windows
windows:
  enabled: true
  times:
    morning: [9, 12]
    afternoon: [13, 17]
    evening: [18, 21]

# Learning loop
learning:
  enabled: true
  algorithm: thompson_sampling
```

## 🎓 Thompson Sampling Learning

The agent learns which topic×time-window×media combinations perform best:

```bash
# Settle metrics for a post (manual)
python src/main.py --settle POST_ID --arm "power-platform|morning|false"

# Settle all posts automatically
python src/main.py --settle-all
```

**How it works:**
1. Creates posts with different topic/time/media combinations
2. Tracks engagement (likes, replies, retweets)
3. Computes reward score (0-1)
4. Updates Beta distribution for each "arm"
5. Biases future choices toward high-performing combinations

## 📊 Budget & Rate Limits

### Monthly Caps by Plan
| Plan | Reads | Writes | Notes |
|------|-------|--------|-------|
| Free | 100 | 500 | Start here |
| Basic | 15,000 | 50,000 | For active use |
| Pro | 1,000,000 | 300,000 | High volume |

### Check Status
```bash
# View budget usage
python src/main.py --safety print-budget

# View rate limits
python src/main.py --safety print-limits
```

## 🚀 Usage Examples

### Post Mode (Time-Window Aware)
```bash
# Post using optimal time window
python src/main.py --mode post --plan free
```

### Interact Mode
```bash
# Search, like, reply based on queries
python src/main.py --mode interact --plan free
```

### Both Modes
```bash
# Post AND interact
python src/main.py --mode both --plan free
```

### Learning Loop
```bash
# Settle metrics after 24 hours
python src/main.py --settle-all
```

## 📝 CLI Reference

```bash
# Main modes
python src/main.py --mode [post|interact|both]

# Auth
python src/main.py --authorize              # OAuth 2.0 only

# Dry run
python src/main.py --dry-run --mode both

# Plan tier
python src/main.py --plan [free|basic|pro]

# Safety commands
python src/main.py --safety [print-budget|print-limits]

# Learning
python src/main.py --settle POST_ID --arm "topic|window|media"
python src/main.py --settle-all
```

## 🔧 Migration from Old Agents

### From agent-x (Tweepy)
1. Copy `.env` credentials
2. Set `auth_mode: tweepy` in config
3. Run normally - all features preserved + new ones added

### From x-agent (OAuth 2.0)
1. Keep `.token.json` file
2. Set `auth_mode: oauth2` in config
3. Run normally - all features preserved + learning added

## 🧪 Testing

```bash
# Smoke tests (dry-run)
python tests/smoke_test.py

# Live test (creates ONE post)
python tests/live_test.py --confirm

# Learning test
python tests/test_learning.py
```

## 📚 Key Improvements

### Over agent-x
- ✅ OAuth 2.0 PKCE support (optional)
- ✅ Better budget manager with plan tiers
- ✅ More comprehensive rate limiting
- ✅ Improved documentation
- ✅ Better error handling

### Over x-agent
- ✅ Tweepy support for simpler auth
- ✅ Thompson Sampling learning loop
- ✅ Time-window scheduling
- ✅ Template-based content
- ✅ Simpler onboarding option

## 🔒 Reliability

This project includes a small reliability layer that hardens OAuth2 (raw HTTP) calls while
keeping Tweepy-based flows unchanged. Key points:

- Timeouts: all raw HTTP calls use an explicit default timeout (DEFAULT_TIMEOUT = 10s) for
  connect/read to avoid hanging network calls.
- Retries: bounded retries are performed with exponential backoff and jitter. Retryable
  statuses are 429 and 500–504.
- Rate-limit handling: when a 429 response includes an `x-rate-limit-reset` header, the
  client will wait until the reset time (capped) before retrying to be polite to the API.
- Idempotency: POST requests automatically include a deterministic `Idempotency-Key`
  derived from the JSON payload (sha256 of canonical JSON). GET and DELETE are not
  automatically idempotent by header.

Rationale: these changes make OAuth2 network interactions safer and more policy-compliant
under transient failures and rate limits. Dry-run behavior is unchanged; Tweepy mode is
untouched and continues to rely on its own retry logic.

## 🎯 Best Practices

### For Free Plan
```yaml
plan: free
windows:
  enabled: true
max_per_window:
  post: 1
  like: 5
  reply: 2
learning:
  enabled: true
```

### For Basic/Pro Plans
```yaml
plan: basic  # or pro
windows:
  enabled: false  # More flexibility
max_per_window:
  post: 5
  like: 20
  reply: 10
learning:
  enabled: true
```

## 📖 Documentation

- **README.md** - This file (overview)
- **QUICKSTART.md** - 5-minute setup guide
- **MIGRATION.md** - Migration from old agents
- **API.md** - API reference and examples
- **LEARNING.md** - Thompson Sampling details

## 🔐 Compliance

- ✅ Only official X API (v2 + v1.1 media)
- ✅ Both auth methods supported
- ✅ Respects all rate limits
- ✅ Enforces plan caps
- ✅ Full audit logging
- ✅ Deduplication
- ✅ Follows X Developer Policy

## 🤝 Contributing

This unified agent combines:
- **agent-x**: Tweepy-based with learning loop
- **x-agent**: OAuth 2.0 with comprehensive safety

Both implementations are preserved in archive/ for reference.

## 📄 License

MIT License - See LICENSE file

---

**Choose your auth, keep your budget, learn what works. Simple.**
