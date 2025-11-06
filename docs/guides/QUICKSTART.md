# Quick Start Guide

Complete step-by-step setup guide for X Agent Unified. Get your unified X agent running in 5 minutes!

> **Overview**: See [README.md](../../README.md) for architecture, features, and configuration reference.

## Prerequisites

- **Python 3.8+** (3.12 recommended)
- **X Developer Account** with approved app
- **Git** (for cloning)
- **VS Code** (recommended) or any editor

## Step 1: Clone & Install

### Windows PowerShell

```powershell
# Clone repository
git clone https://github.com/georgicaradu5-source/Play-stuff.git
cd Play-stuff

# Run setup script
.\setup.bat
```

### Linux/macOS

```bash
# Clone repository
git clone https://github.com/georgicaradu5-source/Play-stuff.git
cd Play-stuff

# Run setup script
chmod +x setup.sh
./setup.sh
```

**What this does:**
- Creates virtual environment (`.venv/`)
- Installs dependencies from `requirements.txt`
- Creates `data/` directory for SQLite database
- Copies `config.example.yaml` -> `config.yaml`

## Step 2: Choose Authentication Method

### Option A: Tweepy (OAuth 1.0a) - Recommended for Beginners

**Pros**: Simple setup, 4 credentials, supports media upload  
**Cons**: Manual token refresh

1. Get credentials from [X Developer Portal](https://developer.x.com/):
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

2. Edit `.env` file:

```bash
X_AUTH_MODE=tweepy
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_token_secret_here
```

### Option B: OAuth 2.0 PKCE - Modern & Recommended for Production

**Pros**: Auto token refresh, granular scopes, modern flow  
**Cons**: Slightly more complex initial setup

1. Get credentials from [X Developer Portal](https://developer.x.com/):
   - Client ID
   - Client Secret

2. Edit `.env` file:

```bash
X_AUTH_MODE=oauth2
X_CLIENT_ID=your_client_id_here
X_CLIENT_SECRET=your_client_secret_here
```

3. Run authorization flow (one-time):

```bash
python src/main.py --authorize
```

This will:
- Open browser for X authorization
- Save refresh token to `.token.json`
- Auto-refresh tokens in future runs

## Step 3: Configure Settings

Edit `config.yaml` to customize behavior:

```yaml
# Choose plan tier (free/basic/pro)
plan: free

# Set auth mode (matches .env setting)
auth_mode: tweepy  # or oauth2

# Define content topics
topics:
  - power-platform
  - data-viz
  - automation

# Configure time windows (optional but recommended)
windows:
  enabled: true
  times:
    morning: [9, 12]
    afternoon: [13, 17]
    evening: [18, 21]

# Enable learning loop
learning:
  enabled: true
  algorithm: thompson_sampling
```

**Key settings:**
- `plan`: Controls monthly budget caps (free/basic/pro)
- `topics`: Content themes for posts
- `windows`: Optimal posting times (leave enabled for free plan)
- `learning.enabled`: Enables Thompson Sampling optimization

## Step 4: Test with Dry-Run

**Always test first!** Dry-run mode simulates actions without making actual API calls.

```bash
# Windows PowerShell
python src\main.py --mode both --dry-run true

# Linux/macOS
python src/main.py --mode both --dry-run true
```

**Expected output:**
```
[DRY-RUN] Would create post: "Exploring Power Platform automation..."
[DRY-RUN] Would like tweet: 1234567890
[DRY-RUN] Metrics: 0 posts, 0 likes, 0 replies
```

## Step 5: Run Live

Once dry-run succeeds, run for real:

```bash
# Post AND interact mode
python src/main.py --mode both --plan free

# Post only
python src/main.py --mode post --plan free

# Interact only (like/reply)
python src/main.py --mode interact --plan free
```

**What happens:**
1. Checks budget and rate limits
2. Selects optimal topic/time-window using Thompson Sampling
3. Creates post or interacts with tweets
4. Logs all actions to SQLite (`data/agent_unified.db`)
5. Tracks engagement for learning loop

## Step 6: Enable Learning (Optional but Recommended)

After posts have been live for 24+ hours, settle metrics to improve future choices:

```bash
# Settle all posts automatically
python src/main.py --settle-all

# Or settle specific post manually
python src/main.py --settle POST_ID --arm "topic|window|media"
```

This updates the Thompson Sampling model with engagement data (likes, replies, retweets).

## Common Issues

### "ModuleNotFoundError: No module named 'dotenv'"

**Solution**: Activate virtual environment first

```powershell
# Windows
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

### "X API authentication failed"

**Solution**: Verify credentials in `.env` and auth mode in `config.yaml` match

### "Budget exceeded for plan 'free'"

**Solution**: Check usage with `python src/main.py --safety print-budget` or wait until next month

### "Rate limit exceeded"

**Solution**: Wait until reset time shown in error, or check with `python src/main.py --safety print-limits`

## Makefile Commands

If you have `make` installed:

```bash
make dev        # Install dependencies in dev mode
make lint       # Run ruff linter
make type       # Run mypy type checker
make test       # Run pytest with coverage
make dry-run    # Dry-run with both modes
make peek       # View recent actions from DB
```

## VS Code Tasks

Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) -> "Tasks: Run Task":

- **Run: Tests (pytest -v)** - Run unit tests
- **Run: Dry-run (both modes)** - Safe dry-run
- **Run: Print Budget** - Check budget usage
- **Run: Print Rate Limits** - Check rate limit status
- **Run: Peek Recent Actions** - View action log

## Next Steps

1. **Automate scheduling**: See [FIRST_TWEET_GUIDE.md](FIRST_TWEET_GUIDE.md) for scheduling tips
2. **Understand budget system**: See [READ_BUDGET.md](READ_BUDGET.md) for plan details
3. **Monitor performance**: Run `scripts/peek_actions.py` to view metrics
4. **Optimize learning**: Regularly run `--settle-all` to improve topic/time choices

## Validation Checklist

Before going live, confirm:

- [ ] `make lint` passes (or `python -m ruff check src/ tests/`)
- [ ] `make type` passes (or `./scripts/mypy.ps1` / `./scripts/mypy.sh`)
- [ ] `make test` passes (or `pytest -v`)
- [ ] Dry-run succeeds with `--dry-run true --mode both`
- [ ] Credentials verified in `.env`
- [ ] Config validated in `config.yaml`
- [ ] Budget checked with `--safety print-budget`

## Getting Help

- **Issues**: Report bugs via [GitHub Issues](https://github.com/georgicaradu5-source/Play-stuff/issues)
- **Documentation**: See [README.md](../../README.md) for full reference
- **Guides**: Check [docs/guides/](.) for additional walkthroughs
- **Compliance**: Review [X Developer Policy](https://developer.x.com/en/developer-terms/policy) and [Automation Rules](https://help.x.com/en/rules-and-policies/x-automation-rules)

---

**Welcome to X Agent Unified!** Start with dry-run, monitor your budget, and let Thompson Sampling optimize your content strategy.

