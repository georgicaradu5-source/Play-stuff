# Agent X (Python + Tweepy)

Production-ready, policy-compliant autonomous agent for X (Twitter) using only the official API (v2 for Tweets/search/interactions, v1.1 for media upload). Includes rate-limit backoff, jitter, SQLite history, basic dedup, optional learning loop, and VS Code setup.

## Features
- Post text (+ optional media via v1.1 upload)
- Search Recent (7-day) and interact (reply, like, follow)
- Bounded actions per time window, randomized order, jitter between calls
- SQLite logging of all actions and post texts to avoid duplicates (7 days)
- Simple bandit learning (Thompson Sampling) to bias topic×window choices
- Dry-run mode prints planned actions without hitting X

## Policy & Safety
- Uses only official X API. No UI scripting.
- Label the account as automated in Profile > About > Automated account.
- Respect X Automation Rules and Developer Policy. No mass-mention/follow. No repeated templates.
- Implements exponential backoff with jitter for rate limits.

## Scopes and Auth (user-context OAuth)
Set these in `.env`:
- tweet.read, tweet.write, users.read, offline.access
- like.read, like.write, follows.read, follows.write
- media.write (for media uploads)

## Setup

### Windows
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r agent-x/requirements.txt
copy agent-x\.env.example agent-x\.env
# fill in credentials in agent-x\.env
python -m agent_x.src.main --help  # if using -m form, ensure PYTHONPATH includes workspace
python agent-x/src/main.py --mode both --dry-run true
```

### Linux/macOS
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r agent-x/requirements.txt
cp agent-x/.env.example agent-x/.env
# fill in credentials in agent-x/.env
python agent-x/src/main.py --mode both --dry-run true
```

VS Code: `.vscode/launch.json` is configured to load `agent-x/.env`.

## Configuration
Edit `agent-x/src/config.example.yaml`:
- topics: ["power-platform", "data-viz", "automation"]
- queries: English and Romanian variants, separated (uses `lang:` operator). Examples included.
- cadence: weekdays [1..5], windows [morning, afternoon, evening]
- max_per_window: post, reply, like, follow limits
- jitter_seconds: e.g., [8, 20]

Free tier: use `agent-x/src/config.free.yaml` to enable caps and watchlist-first strategy. The agent enforces monthly caps (create=500, read=100 by default) via SQLite counters and gates likes/follows via `feature_flags`.

## Running
- Dry run (no API calls):
```
python agent-x/src/main.py --mode both --dry-run true
```
- Post only:
```
python agent-x/src/main.py --mode post --dry-run false
```
- Interact only:
```
python agent-x/src/main.py --mode interact --dry-run false
```

## Learning Loop
- Settle one post with an arm (topic|window|mediaFlag):
```
python agent-x/src/main.py --settle 1234567890 --arm power-platform|morning|False
```
- Settle all posts (best-effort):
```
python agent-x/src/main.py --settle-all
```
Stores public engagement metrics and updates a Beta bandit.

## Smoke Test
Quick API sanity check for Recent Search:
```
python agent-x/smoke.py
```

## Notes
- Recent Search is a rolling 7-day window.
- Media: v1.1 `media/upload` + v2 `POST /2/tweets` with `media_ids`.
- The agent logs every action in `agent-x/data/agent.db`.
- To avoid duplicates, recent post text is normalized and checked for exact/near-duplicate tokens.
 - Free mode caps: counts Tweet creates (posts+replies+retweets) and reads (number of posts returned). Watchlist timelines are cheaper than broad search.
