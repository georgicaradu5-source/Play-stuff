# X Agent Deep Dive

This doc summarizes loops, components, and behaviors for the unified X agent.

## Components

- `src/auth.py` — Dual auth (Tweepy OAuth1; OAuth2 PKCE); tokens persisted to `.token.json` for OAuth2
- `src/x_client.py` — Unified client wrapping requests; integrates retry logic and tracing
- `src/rate_limiter.py` — Per-endpoint tracking and jittered backoff
- `src/storage.py` — SQLite state: actions, metrics, monthly usage, dedup, bandit tables
- `src/scheduler.py` — Time-window orchestration (morning/afternoon/evening)
- `src/learn.py` — Thompson Sampling across (topic | window | media) arms
- `src/telemetry.py` — Optional OpenTelemetry spans with no-op fallback
- `src/actions.py` — Content generation and action entrypoints
- `src/main.py` — CLI/flags and modes; dry-run support

## Loops

1. Schedule → Select window → Choose candidate content
2. Deduplicate via Jaccard + hash
3. If not dry-run, post/like via client; otherwise log & artifact
4. Update storage and learning metrics; repeat per window

## Behavior notes

- Media upload is Tweepy-only (v1.1); OAuth2 raises `NotImplementedError`
- Retry semantics for 429/5xx; honor `x-rate-limit-reset` and use Idempotency-Key for POSTs
- Telemetry spans wrap key operations; safe to enable/disable

## Areas to improve

- Expand tracing coverage (scheduler + learning loop)
- Optional devcontainer and Codespaces setup
- Plug-in model selection per topic/time window
