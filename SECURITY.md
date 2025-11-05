# Security Policy

## Supported Versions
We support the latest `main` branch.

## Reporting a Vulnerability
Please do not open a public issue for security vulnerabilities. Instead:
- Email the maintainers (see repository owners), or
- Open a private security advisory via GitHub (Security tab → Report a vulnerability)

We aim to triage within 2 business days.

## Secrets and Credentials
- Do not commit secrets. `.env` and `.token.json` are ignored via `.gitignore`.
- Use GitHub Environments for production/staging secrets (see `docs/ENVIRONMENTS.md`).

## Dependencies
- Dependabot is enabled to propose updates automatically.
