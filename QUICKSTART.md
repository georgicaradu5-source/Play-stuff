# X Agent Unified - Quick Start

Get your unified X agent running in 5 minutes!

## Prerequisites

- Python 3.9+
- X (Twitter) Developer Account
- API credentials (OAuth 1.0a or OAuth 2.0)

## Quick Setup

### Windows

```powershell
# Run setup script
.\setup.bat

# Edit credentials
notepad .env

# Test with dry run
python src\main.py --mode both --dry-run true

# Run for real
python src\main.py --mode both
```

### Mac/Linux

```bash
# Run setup script
chmod +x setup.sh
./setup.sh

# Edit credentials
nano .env

# Test with dry run
python src/main.py --mode both --dry-run true

# Run for real
python src/main.py --mode both
```

## Choose Your Auth Mode

### Option A: Tweepy (OAuth 1.0a) - Simpler

1. Edit `.env`:
   ```
   X_AUTH_MODE=tweepy
   X_API_KEY=your_api_key
   X_API_SECRET=your_api_secret
   X_ACCESS_TOKEN=your_access_token
   X_ACCESS_SECRET=your_access_secret
   ```

2. Run:
   ```bash
   python src/main.py --mode both --dry-run true
   ```

### Option B: OAuth 2.0 PKCE - Modern

1. Edit `.env`:
   ```
   X_AUTH_MODE=oauth2
   X_CLIENT_ID=your_client_id
   X_CLIENT_SECRET=your_client_secret
   ```

2. Authorize:
   ```bash
   python src/main.py --authorize
   ```

3. Run:
   ```bash
   python src/main.py --mode both --dry-run true
   ```

## Common Commands

```bash
# Post mode only
python src/main.py --mode post

# Interact mode only (like, reply, follow)
python src/main.py --mode interact

# Both modes
python src/main.py --mode both

# Dry run (no actual API calls)
python src/main.py --mode both --dry-run true

# Check budget status
python src/main.py --safety print-budget

# Check learning stats
python src/main.py --safety print-learning

# Settle metrics for learning
python src/main.py --settle-all

# Use specific config
python src/main.py --config my-config.yaml
```

## Configuration

Edit `config.yaml` to customize:

- **Topics**: Content themes
- **Queries**: Search terms for interaction
- **Schedule**: Time windows (morning/afternoon/evening)
- **Limits**: Max actions per window
- **Learning**: Enable/disable Thompson Sampling
- **Budget**: Plan tier and safety buffer

## Learning Loop

The agent learns which (topic, time-window, media) combinations work best:

1. Run posts: `python src/main.py --mode post`
2. Wait for engagement (hours/days)
3. Settle metrics: `python src/main.py --settle-all`
4. Check stats: `python src/main.py --safety print-learning`

The agent will favor high-performing combinations!

## Troubleshooting

### "Missing X API credentials"
- Check `.env` file exists and has correct variables
- For Tweepy: need all 4 credentials (API key/secret, access token/secret)
- For OAuth2: need client ID/secret, run `--authorize` first

### "Budget exceeded"
- Check current usage: `python src/main.py --safety print-budget`
- Adjust plan in `config.yaml` or `.env`
- Increase buffer: set `budget.buffer_pct: 0.1` in config

### "Rate limit exceeded"
- Agent has built-in rate limiting with backoff
- For persistent issues, reduce limits in `config.yaml`

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Customize `config.yaml` for your use case
3. Set up automation (cron/Task Scheduler)
4. Enable learning loop for optimization

## Support

- Issues: https://github.com/georgicaradu5-source/Play-stuff/issues
- Docs: See README.md for architecture details
