# Quick Start Guide# X Agent Unified - Quick Start



Complete step-by-step setup guide for X Agent Unified.Get your unified X agent running in 5 minutes!



> **📖 Overview**: See [README.md](../../README.md) for architecture, features, and configuration reference.## Prerequisites



## Prerequisites- Python 3.9+

- X (Twitter) Developer Account

- **Python 3.8+** (3.12 recommended)- API credentials (OAuth 1.0a or OAuth 2.0)

- **X Developer Account** with approved app

- **Git** (for cloning)## Quick Setup

- **VS Code** (recommended) or any editor

### Windows

## Step 1: Clone & Install

```powershell

```powershell# Run setup script

# Windows PowerShell.\setup.bat

git clone https://github.com/georgicaradu5-source/Play-stuff.git

cd Play-stuff# Edit credentials

.\setup.batnotepad .env

```

# Test with dry run

```bashpython src\main.py --mode both --dry-run true

# Linux/macOS

git clone https://github.com/georgicaradu5-source/Play-stuff.git# Run for real

cd Play-stuffpython src\main.py --mode both

chmod +x setup.sh && ./setup.sh```

```

### Mac/Linux

**What this does:**

- ✅ Creates virtual environment (`.venv/`)```bash

- ✅ Installs dependencies from `requirements.txt`# Run setup script

- ✅ Creates `data/` directory for SQLite databasechmod +x setup.sh

- ✅ Copies `config.example.yaml` → `config.yaml`./setup.sh



## Step 2: Choose Authentication Method# Edit credentials

nano .env

### Option A: Tweepy (OAuth 1.0a) — Recommended for Beginners

# Test with dry run

**Pros**: Simple setup, 4 credentials, supports media upload  python src/main.py --mode both --dry-run true

**Cons**: Manual token management

# Run for real

1. **Get credentials** from [X Developer Portal](https://developer.twitter.com/):python src/main.py --mode both

   - API Key```

   - API Secret

   - Access Token## Choose Your Auth Mode

   - Access Token Secret

### Option A: Tweepy (OAuth 1.0a) - Simpler

2. **Create `.env` file** in project root:

   ```env1. Edit `.env`:

   X_AUTH_MODE=tweepy   ```

   X_API_KEY=your_api_key_here   X_AUTH_MODE=tweepy

   X_API_SECRET=your_api_secret_here   X_API_KEY=your_api_key

   X_ACCESS_TOKEN=your_access_token_here   X_API_SECRET=your_api_secret

   X_ACCESS_SECRET=your_access_token_secret_here   X_ACCESS_TOKEN=your_access_token

   ```   X_ACCESS_SECRET=your_access_secret

   ```

3. **Skip to Step 3**

2. Run:

### Option B: OAuth 2.0 PKCE — Recommended for Production   ```bash

   python src/main.py --mode both --dry-run true

**Pros**: Modern, automatic token refresh, granular scopes     ```

**Cons**: Requires authorization flow, limited media support

### Option B: OAuth 2.0 PKCE - Modern

1. **Get credentials** from [X Developer Portal](https://developer.twitter.com/):

   - Client ID1. Edit `.env`:

   - Client Secret   ```

   - Set redirect URI: `http://localhost:8080/callback`   X_AUTH_MODE=oauth2

   X_CLIENT_ID=your_client_id

2. **Create `.env` file** in project root:   X_CLIENT_SECRET=your_client_secret

   ```env   ```

   X_AUTH_MODE=oauth2

   X_CLIENT_ID=your_client_id_here2. Authorize:

   X_CLIENT_SECRET=your_client_secret_here   ```bash

   X_REDIRECT_URI=http://localhost:8080/callback   python src/main.py --authorize

   ```   ```



3. **Run authorization flow**:3. Run:

   ```bash   ```bash

   python src/main.py --authorize   python src/main.py --mode both --dry-run true

   ```   ```

   

   - Opens browser for X login## Common Commands

   - Grants permissions to your app

   - Saves tokens to `.token.json` (gitignored)```bash

# Post mode only

## Step 3: Configure Settingspython src/main.py --mode post



Edit `config.yaml` to customize behavior:# Interact mode only (like, reply, follow)

python src/main.py --mode interact

```yaml

# Authentication mode (must match .env)# Both modes

auth_mode: tweepy  # or oauth2python src/main.py --mode both



# Plan tier (enforces monthly limits)# Dry run (no actual API calls)

plan: free  # or basic, propython src/main.py --mode both --dry-run true



# Topics for content generation# Check budget status

topics:python src/main.py --safety print-budget

  - power-platform

  - data-viz# Check learning stats

  - automationpython src/main.py --safety print-learning

  - ai

# Settle metrics for learning

# Search queries for interaction modepython src/main.py --settle-all

queries:

  - query: '(Power BI OR "Power Platform") lang:en -is:retweet'# Use specific config

    actions: [like, reply]python src/main.py --config my-config.yaml

```

# Time windows (when to post)

schedule:## Configuration

  windows:

    - morning    # 9am-12pmEdit `config.yaml` to customize:

    - afternoon  # 1pm-5pm

    - evening    # 6pm-9pm- **Topics**: Content themes

- **Queries**: Search terms for interaction

# Weekday posting (1=Monday, 7=Sunday)- **Schedule**: Time windows (morning/afternoon/evening)

cadence:- **Limits**: Max actions per window

  weekdays: [1, 2, 3, 4, 5]- **Learning**: Enable/disable Thompson Sampling

- **Budget**: Plan tier and safety buffer

# Action limits per time window

max_per_window:## Learning Loop

  post: 1

  reply: 3The agent learns which (topic, time-window, media) combinations work best:

  like: 10

  follow: 31. Run posts: `python src/main.py --mode post`

2. Wait for engagement (hours/days)

# Learning loop (optimize based on engagement)3. Settle metrics: `python src/main.py --settle-all`

learning:4. Check stats: `python src/main.py --safety print-learning`

  enabled: true

```The agent will favor high-performing combinations!



## Step 4: Test with Dry-Run## Troubleshooting



**Always test first!** Dry-run mode simulates actions without calling the X API.### "Missing X API credentials"

- Check `.env` file exists and has correct variables

```bash- For Tweepy: need all 4 credentials (API key/secret, access token/secret)

# Test both post and interact modes- For OAuth2: need client ID/secret, run `--authorize` first

python src/main.py --dry-run true --mode both

```### "Budget exceeded"

- Check current usage: `python src/main.py --safety print-budget`

**Expected output:**- Adjust plan in `config.yaml` or `.env`

```- Increase buffer: set `budget.buffer_pct: 0.1` in config

[DRY-RUN] Would create post: "Just discovered a cool trick with Power BI..."

[DRY-RUN] Would like tweet: 1234567890123456789### "Rate limit exceeded"

[DRY-RUN] Would reply to tweet: 9876543210987654321- Agent has built-in rate limiting with backoff

```- For persistent issues, reduce limits in `config.yaml`



**Verify in database:**## Next Steps

```bash

# View recent actions (should be empty in dry-run)1. Read [README.md](README.md) for full documentation

python scripts/peek_actions.py --limit 102. Customize `config.yaml` for your use case

```3. Set up automation (cron/Task Scheduler)

4. Enable learning loop for optimization

## Step 5: Run Live (First Tweet)

## Support

> ⚠️ **Warning**: This will create real posts/interactions on X. Start with post mode only.

- Issues: https://github.com/georgicaradu5-source/Play-stuff/issues

```bash- Docs: See README.md for architecture details

# Post mode only (safest)
python src/main.py --mode post --plan free
```

**First run checklist:**
- ✅ Dry-run tested successfully
- ✅ Config reviewed (especially topics and windows)
- ✅ Database created (`data/agent_unified.db` exists)
- ✅ Credentials valid (no auth errors in dry-run)

**Monitor progress:**
```bash
# Check budget usage
python src/main.py --safety print-budget

# Check rate limits
python src/main.py --safety print-limits

# View recent actions
python scripts/peek_actions.py --limit 5 --kind post
```

## Step 6: Enable Learning Loop (Optional)

After 24-48 hours, settle metrics to improve performance:

```bash
# Fetch engagement metrics and update learning
python src/main.py --settle-all
```

**What this does:**
- Fetches likes, replies, retweets for each post
- Calculates reward score (0-1)
- Updates Thompson Sampling bandit for topic/window/media combinations
- Future posts favor high-performing patterns

## Common Issues

### Authentication Fails

**Tweepy Mode:**
- Verify all 4 credentials in `.env`
- Check app has read/write permissions in X Developer Portal
- Ensure tokens aren't expired

**OAuth2 Mode:**
- Re-run `python src/main.py --authorize`
- Check redirect URI matches exactly (`http://localhost:8080/callback`)
- Verify `.token.json` exists after authorization

### No Posts Created

- Check if current time matches configured windows (morning/afternoon/evening)
- Verify weekday is in `cadence.weekdays` (e.g., `[1,2,3,4,5]` = Mon-Fri)
- Check budget: `python src/main.py --safety print-budget`
- Look for errors in console output

### Rate Limit Errors

- Agent automatically handles rate limits with backoff
- If persistent, reduce `max_per_window` values in config
- Check current limits: `python src/main.py --safety print-limits`

## Makefile Commands (Dev Container)

If using the Dev Container or have `make` installed:

```bash
make dev        # Install dependencies
make test       # Run unit tests
make dry-run    # Safe dry-run test
make budget     # Print budget status
make limits     # Print rate limits
make peek       # View recent actions
make lint       # Run ruff linter
make type       # Run mypy type checker
make clean      # Clean cache/artifacts
```

## VS Code Tasks

Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → "Run Task":

- **Run Tests** (default test task)
- **Dry-Run Agent**
- **Print Budget**
- **Print Rate Limits**
- **Peek Recent Actions**
- **Lint**
- **Type Check**

## Next Steps

- **First Tweet**: See [FIRST_TWEET_GUIDE.md](FIRST_TWEET_GUIDE.md) for detailed first tweet workflow
- **Budget Management**: See [READ_BUDGET.md](READ_BUDGET.md) for understanding plan limits
- **Learning Loop**: Let agent run for 1-2 weeks, then review bandit performance
- **Advanced Config**: Explore `config.*.yaml` examples for different use cases

## Validation Checklist

Before enabling live mode, run these validation commands:

```bash
# ✅ Lint code (check style)
make lint  # or: nox -s lint

# ✅ Type check (verify types)
make type  # or: nox -s type

# ✅ Run tests (18 should pass, 2 skip)
make test  # or: pytest -v

# ✅ Dry-run both modes (no errors)
python src/main.py --dry-run true --mode both
```

**All checks passing?** You're ready for production! 🚀

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/georgicaradu5-source/Play-stuff/issues)
- **Docs**: [docs/](../) directory
- **Contributing**: See [CONTRIBUTING.md](../../CONTRIBUTING.md)
