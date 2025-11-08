# Improvements Roadmap (Mirror of Strategic Checklists)

This document mirrors the top improvement checklists from the strategic notebook so they’re easy to scan and turn into issues.

## Modularization
- [ ] Inventory tightly coupled logic in `src/x_client.py` and `src/actions.py`
- [ ] Extract API, business logic, and orchestration into modules
- [ ] Add/expand unit tests for new modules
- [ ] Update docs to reflect new boundaries

## Telemetry Expansion
- [ ] Audit current tracing coverage
- [ ] Add spans for auth, post, like, rate limiter, storage
- [ ] Inject trace context into logs
- [ ] Validate end-to-end with OTLP endpoint

## Rate Limiter Integration
- [ ] Route all client actions through rate limiter (pre/post checks)
- [ ] Log backoff/jitter decisions and limiter hits
- [ ] Add tests for burst traffic and 429 recovery
- [ ] Document integration contract

## Security Hardening
- [ ] Review token handling and storage; rotate secrets policy
- [ ] Prevent sensitive data in logs/exceptions
- [ ] Harden external API boundaries and input validation
- [ ] Add security-focused tests (red team cases)

## Learning Loop Refinement
- [ ] Tune Thompson Sampling priors/parameters
- [ ] Expand bandit metrics and logging
- [ ] Simulate varied scenarios and edge cases
- [ ] Document learnings and update defaults

## Process
- Convert each checked item into an Issue (label: `improvement`, plus component label)
- Reference related notebook sections and test IDs
- Track status here until issues are created

## Milestone
Progress tracked in GitHub milestone: [Strategic Enhancements v1.2.0](https://github.com/georgicaradu5-source/Play-stuff/milestone/2)

**Associated Issues:**
- [#38 Modularization](https://github.com/georgicaradu5-source/Play-stuff/issues/38)
- [#39 Telemetry Expansion](https://github.com/georgicaradu5-source/Play-stuff/issues/39)
- [#40 Rate Limiter Integration](https://github.com/georgicaradu5-source/Play-stuff/issues/40)
- [#41 Security Hardening](https://github.com/georgicaradu5-source/Play-stuff/issues/41)
- [#42 Learning Loop Refinement](https://github.com/georgicaradu5-source/Play-stuff/issues/42)

**Timeline:** Due November 22, 2025 (14 days)

**Resources:**
- [Live Progress Status](STATUS.md) — Auto-updated daily
- [Execution Plan](EXECUTION_PLAN.md) — Recommended sequence, branching, and validation steps
