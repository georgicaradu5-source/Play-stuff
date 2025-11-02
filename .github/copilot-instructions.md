<!-- Repo-level guidance for AI coding agents working in this repo. Keep it concise and concrete. -->

# Copilot instructions — Play-stuff (Unified X Agent)

This repo contains a production-ready autonomous X (Twitter) agent with dual authentication and safety controls. Use only the official X APIs (v2 + v1.1 media) and respect automation/rate-limit rules.

## Architecture (where to look)
- `src/auth.py` — Dual auth. Tweepy OAuth 1.0a and OAuth 2.0 PKCE. Tokens persist to `.token.json` in OAuth2.
- `src/x_client.py` — Unified client. Switches per mode; uses `reliability.request_with_retries` and `telemetry.start_span`.
- `src/budget.py` — Plan caps (free/basic/pro) and safety buffers; integrates with storage usage.
- `src/rate_limiter.py` — Per-endpoint tracking + backoff/jitter; prefer calling via `XClient`.
- `src/storage.py` — SQLite at `data/agent_unified.db`; action log, metrics, monthly usage, dedup (hash + Jaccard), bandit tables.
- `src/scheduler.py` — Time-window posting (morning/afternoon/evening) and orchestration.
- `src/learn.py` — Thompson Sampling across (topic | window | media) “arms”.
- `src/telemetry.py` — Optional OpenTelemetry tracing with no-op fallback; W3C TraceContext injected into logs.
- Entry point: `src/main.py` (CLI flags), content: `src/actions.py`. Config schema: `src/config_schema.py`.

## Day‑1 developer workflows (Windows PowerShell)
- Setup: `./setup.bat`, then edit `.env`. Choose auth: `$env:X_AUTH_MODE = 'tweepy' | 'oauth2'`.
- OAuth2 authorize once: `python src/main.py --authorize` (stores `.token.json`).
- Dry‑run safe test: `python src/main.py --mode both --dry-run true` (never posts/likes).
- VS Code tasks: “Run: Dry-run (both modes)”, “Run: Tests (pytest -v)”.
- Type check: `./scripts/mypy.ps1` (Linux/macOS: `./scripts/mypy.sh`). Optional: `nox -s lint type test`.

## Project conventions and gotchas
- Always go through `XClient` + `UnifiedAuth`; don’t handcraft HTTP unless adding a new endpoint (then use `request_with_retries`).
- Media upload (v1.1) works only in Tweepy mode; raise `NotImplementedError` in OAuth2.
- Rate-limit/backoff: retries for 429/5xx, honors `x-rate-limit-reset` when present; POSTs include deterministic `Idempotency-Key`.
- Storage dedup: avoid spam by checking `Storage.is_text_duplicate(text, days=7)` before posting.
- Learning loop: settle/update metrics via CLI (`--settle*`) and `Storage.bandit_update`.
- Telemetry: enable with `$env:ENABLE_TELEMETRY='true'`; optional `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`.
- Config lives in `config.yaml` (see `config.example.yaml`); env loaded via `python-dotenv` from `.env`.

## Tests and quality gates
- Run unit tests: `pytest -v` (task provided). Tests cover auth, budget, rate limiting, storage, telemetry/tracing spans, reliability, and client behavior.
- Prefer dry‑run in tests and scripts; no network calls unless explicitly marked live.
- Keep both auth modes working; add tests for new behavior in each mode when applicable.

## Integration boundaries
- External libs: Tweepy (OAuth 1.0a), `requests` (OAuth2), `python-dotenv`, optional OpenTelemetry SDK/exporters.
- X API v2 for core endpoints; v1.1 only for media upload via Tweepy.

Tip: When adding an API call, implement in `XClient` with a span, call `request_with_retries`, plumb rate-limit metadata to `storage.log_action`, and honor `dry_run` behavior.
- Both are kept for reference in `_archive/` directory
