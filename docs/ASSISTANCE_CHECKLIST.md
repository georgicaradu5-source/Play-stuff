# Assistance Checklist

Items requiring user/environment input before scaling beyond current scope.

| Area | Input Needed | Description |
| ---- | ------------ | ----------- |
| Credentials | Production X API keys | Provide elevated rate-limit keys if higher throughput required |
| Telemetry | OTLP endpoint & service name | For enabling distributed tracing export |
| Observability | Logging backend | Decide on external log aggregation (e.g., ELK / Azure Monitor) |
| Deployment | Target runtime | Codespaces vs. self-hosted runner vs. container orchestrator |
| Media | Asset library path | For image/video posting workflows in Tweepy mode |
| Compliance | Data retention policy | Define how long to keep SQLite historical rows |
| Security | Vulnerability management process | Confirm SLA for dependency CVE response |

Update as new dependencies or operational needs arise.
