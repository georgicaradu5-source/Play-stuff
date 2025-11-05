## PR checklist

- [ ] Title follows Conventional Commits when possible (feat:, fix:, docs:, chore:, refactor:)
- [ ] Linked issue(s) referenced in the description (Closes #123)
- [ ] Tests updated or added; local run of "Run: Tests (pytest -v)" is green
- [ ] Dry-run gate verified locally: `python src/main.py --mode both --dry-run true`
- [ ] Docs updated (README and/or docs/*)
- [ ] No secrets/config in diff (.env, .token.json, access keys)
- [ ] Touches X API? Honored dry_run and used XClient with retries + rate limiter
- [ ] Telemetry spans wrapped (optional) and no-op safe

### Summary

Describe what changed and why. Include screenshots/logs for relevant behaviors.

### Testing notes

Steps, commands, or evidence of local runs. Attach artifact snippets if helpful.
