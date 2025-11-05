# Outside-the-box Opportunities

High-impact, low-risk enhancements to consider next.

1. Multi-model content selection
   - Add provider abstraction to try different LLMs per topic/time window; pick best via Thompson Sampling feedback.
2. Tracing-first development
   - Expand spans across scheduler/learn/client; surface run and action IDs in logs for correlation.
3. Dev Container / Codespaces
   - Provide `.devcontainer` for one-click, reproducible env with Python, nox, and test tasks wired.
4. Caching & rate-limit smoothing
   - Cache recent GETs; smooth spikes via token bucket layered over backoff.
5. Observability dashboards
   - Minimal Grafana dashboards fed by OTEL collector (optional) for success/failure, rate-limit, and budget metrics.

Prioritize by ROI and safety: start with tracing expansion and devcontainer.
