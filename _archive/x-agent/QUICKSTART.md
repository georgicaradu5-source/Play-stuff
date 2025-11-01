# Quick Start Guide - X Agent

Get up and running with X Agent in 5 minutes.

## Prerequisites
- Python 3.9+
- X Developer account ([Sign up here](https://developer.twitter.com/en/portal/petition/essential/basic-info))

## 1. Installation (Windows)

```powershell
cd x-agent

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

```powershell
# Copy environment template
copy .env.example .env

# Copy config template
copy config.example.yaml config.yaml
```

**Edit `.env`** with your X API credentials:
```env
X_CLIENT_ID=your_client_id_here
X_CLIENT_SECRET=your_client_secret_here
```

**Edit `config.yaml`** to customize queries and topics.

## 3. Authorization

```powershell
# Run OAuth flow (opens browser)
python src/main.py --authorize
```

Follow the browser prompts. Tokens will be saved to `.token.json`.

## 4. Test Run (Dry Run)

```powershell
# Test without making real API calls
python src/main.py --dry-run --mode both
```

You should see output like:
```
[DRY RUN] create_post(text='...', ...)
[DRY RUN] search_recent(query='...', max_results=5)
```

## 5. First Production Run

```powershell
# Create 1-2 posts
python src/main.py --mode post --plan free
```

Check your X account - you should see the posts!

## 6. Check Status

```powershell
# View budget usage
python src/main.py --safety print-budget

# View rate limits
python src/main.py --safety print-limits
```

## Next Steps

- Customize `config.yaml` with your topics and queries
- Schedule regular runs with Task Scheduler
- Monitor `data/x_agent.db` for action logs
- Read the full [README.md](README.md) for advanced usage

## Common Commands

```powershell
# Post only
python src/main.py --mode post --plan free

# Interact only (search, like, reply)
python src/main.py --mode interact --plan free

# Both
python src/main.py --mode both --plan free

# Settle metrics
python src/main.py --mode settle-metrics

# Dry run testing
python src/main.py --dry-run --mode both
```

## Troubleshooting

**"No module named 'dotenv'"**
```powershell
pip install -r requirements.txt
```

**"Authorization failed"**
- Check `.env` has correct CLIENT_ID and CLIENT_SECRET
- Verify callback URL is `http://localhost:8080/callback` in X Developer Portal
- Re-run `python src/main.py --authorize`

**"Budget exceeded"**
- Check usage: `python src/main.py --safety print-budget`
- Wait for next month or upgrade plan
- Reduce `max_per_run` in `config.yaml`

## Need Help?

See the full [README.md](README.md) for:
- Architecture details
- All available endpoints
- Query operators reference
- Compliance guidelines
- Scheduling setup
