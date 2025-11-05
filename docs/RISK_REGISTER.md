# Risk Register

Track key risks, likelihood, impact, and mitigations for the X agent.

| ID | Risk | Likelihood | Impact | Mitigation |
| -- | ---- | ---------- | ------ | ---------- |
| R1 | X API rate limits (429) | Medium | Medium | Centralized `request_with_retries`, backoff/jitter, honor `x-rate-limit-reset`, idempotency keys |
| R2 | Credential leakage | Low | High | Secrets in `.env`/repo secrets only; `.gitignore` covers `.env` and `.token.json`; reviews via PR template |
| R3 | Unintended posting | Low | High | Default to dry‑run in CI; required dry‑run gate; dedup via `Storage.is_text_duplicate` |
| R4 | OAuth2 media upload gap | High | Low | Media upload supported only in Tweepy mode; OAuth2 raises `NotImplementedError` by design |
| R5 | DB corruption/locking | Low | Medium | SQLite WAL mode (default OS), small writes; artifacts include DB tail for quick triage |
| R6 | Dependency regressions | Medium | Medium | Dependabot weekly; pinned ranges in `requirements.txt`; tests + dry‑run gate |
| R7 | Observability blind spots | Medium | Low | Optional OTEL tracing with no‑op fallback; spans around client calls |
| R8 | CI flakiness | Low | Low | Retries in tests where appropriate; small coverage threshold; deterministic dry‑run |

Review quarterly and on significant changes.
