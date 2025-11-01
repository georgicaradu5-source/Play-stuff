<!--
Repo-level Copilot instructions for the "Play-stuff" repository.
Contains X Agent Unified: a production-ready autonomous X (Twitter) agent in Python.
-->

# Copilot instructions — Play-stuff

## Project overview
- **Main project**: Unified Python X (Twitter) agent with dual auth support
- **Architecture**: Modular design with dual authentication, learning loop, budget management, and SQLite storage
- **Policy compliance**: Uses only official X API (v2 + v1.1 media), implements rate limiting, respects X automation rules

## Key directories and files
- `src/` — Core Python modules:
  - `main.py` — CLI entry point with all flags
  - `auth.py` — Dual auth (Tweepy OAuth 1.0a + OAuth 2.0 PKCE)
  - `x_client.py` — Unified X API client supporting both auth modes
  - `budget.py` — Enhanced budget manager with plan tiers
  - `rate_limiter.py` — Per-endpoint rate limiting with backoff
  - `storage.py` — Unified SQLite storage with learning tables
  - `scheduler.py` — Time-window scheduling + action orchestration
  - `actions.py` — Template-based content generation
  - `learn.py` — Thompson Sampling learning loop
- `requirements.txt` — Dependencies (tweepy, requests, python-dotenv, PyYAML)
- `.env.example` — Environment template for both auth modes
- `config.example.yaml` — Configuration template with all features

## Essential workflows
### Setup (Windows PowerShell)
```powershell
.\setup.bat
# Edit .env with credentials
# Choose auth mode: X_AUTH_MODE=tweepy or X_AUTH_MODE=oauth2
```

### Run commands
```powershell
# Tweepy mode (OAuth 1.0a) - simple setup
$env:X_AUTH_MODE="tweepy"
python src/main.py --mode both --dry-run true

# OAuth 2.0 PKCE mode - modern auth
$env:X_AUTH_MODE="oauth2"
python src/main.py --authorize
python src/main.py --mode both --dry-run true

# Learning loop
python src/main.py --settle-all
python src/main.py --safety print-learning
```

## Architecture patterns
- **Dual Authentication**: `auth.py` supports both Tweepy (OAuth 1.0a) and OAuth 2.0 PKCE via `X_AUTH_MODE`
- **Unified Client**: `x_client.py` wraps both Tweepy and raw requests, switching based on auth mode
- **Rate Limiting**: `rate_limiter.py` tracks per-endpoint limits with exponential backoff + jitter
- **Budget Management**: `budget.py` supports Free/Basic/Pro tiers with configurable safety buffers
- **Deduplication**: `storage.py` uses hash-based + Jaccard similarity checks (7-day window)
- **Learning**: Thompson Sampling bandit in `learn.py` optimizes (topic, time-window, media) choices
- **Time Windows**: `scheduler.py` manages morning/afternoon/evening posting slots
- **Modularity**: Each module has clear responsibilities, easy to extend

## Development guidelines
- Always test with `--dry-run true` before production runs
- Environment variables loaded from `.env` (never commit credentials)
- Config in `config.yaml` for behavior customization
- Both auth modes are equally supported—don't assume one over the other
- Learning is optional (can be disabled in config)
- Follow X Developer Policy: label account as automated, no mass actions, respect rate limits

## When editing code
- Preserve dual auth support (both Tweepy and OAuth 2.0 must work)
- Maintain modular structure (don't merge unrelated functionality)
- Keep rate limiting and policy compliance in all API interactions
- Test configuration changes with dry-run mode first
- Update `README.md` if adding features or changing setup
- Ensure backward compatibility with both auth modes

## Legacy agents (reference only)
- `_archive/agent-x/` — Original Tweepy-based with learning (superseded by unified)
- `_archive/x-agent/` — OAuth 2.0 PKCE with safety features (superseded by unified)
- Both are kept for reference in `_archive/` directory
