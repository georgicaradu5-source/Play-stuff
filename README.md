
# X Agent - Unified Production-Ready Autonomous X (Twitter) Agent

[![CI](https://github.com/georgicaradu5-source/Play-stuff/actions/workflows/ci.yml/badge.svg)](https://github.com/georgicaradu5-source/Play-stuff/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/georgicaradu5-source/Play-stuff/branch/main/graph/badge.svg)](https://codecov.io/gh/georgicaradu5-source/Play-stuff)
[![CodeQL](https://github.com/georgicaradu5-source/Play-stuff/actions/workflows/codeql.yml/badge.svg)](https://github.com/georgicaradu5-source/Play-stuff/actions/workflows/codeql.yml)
[![Release Draft](https://img.shields.io/badge/release-drafter-blue?logo=github)](https://github.com/georgicaradu5-source/Play-stuff/releases)
[![Dev Container Ready](https://img.shields.io/badge/devcontainer-ready-success?logo=visualstudiocode)](.devcontainer/devcontainer.json)
[![Open in GitHub Codespaces](https://img.shields.io/badge/Codespaces-open-blue?logo=github)](https://codespaces.new/georgicaradu5-source/Play-stuff)

> **Coverage monitoring:** Test coverage is tracked with [Codecov](https://codecov.io/gh/georgicaradu5-source/Play-stuff). Current coverage: **97.8%** with a 97.7% quality gate enforced via `pytest.ini`.

> ### TL;DR / Start Here
> 1. Read: [`docs/guides/QUICKSTART.md`](docs/guides/QUICKSTART.md) (5‑minute setup) · [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) (ops & gates) · [`docs/ENVIRONMENTS.md`](docs/ENVIRONMENTS.md) (GitHub environments & secrets)
> 2. Core validation commands:
>    * `nox -s all` – lint + type + tests
>    * `python src/main.py --dry-run --mode both` – full safety simulation
>    * `python scripts/peek_actions.py --limit 10` – inspect recent DB actions
> 3. Contribute using dry-run first; never post live without validating budget & rate limits.


A fully unified, production-ready autonomous agent for X (Twitter) that combines the best features from both implementations. Supports **both OAuth 1.0a (Tweepy) and OAuth 2.0 PKCE** authentication methods.

## Production Readiness

- Required branch checks enforced: unit tests and dry-run safety gate
- Automated security scanning (CodeQL) and dependency updates (Dependabot)
- Draft release notes generated on each push to `main` (Release Drafter)
- See the full checklist in [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md)

### Dev Container

Open in GitHub Codespaces or locally with the provided Dev Container (`.devcontainer/devcontainer.json`) to get:

- Python 3.12 base image with preinstalled system tools (git, sqlite3, jq)
- Pre-installed: `pytest`, `nox`, `ruff`, `mypy`, `gh` CLI
- Auto-configured pytest test discovery and recommended VS Code extensions

Launch: VS Code -> "Reopen in Container" (or [create a new Codespace](https://codespaces.new/georgicaradu5-source/Play-stuff)). Then:
```bash
make dev        # Install project dependencies
make test       # Run unit tests
make dry-run    # Safe dry-run with both modes
make peek       # View recent actions from DB
```

VS Code tasks are also available (Terminal -> Run Task): "Run Tests", "Dry-Run Agent", "Print Budget", "Print Rate Limits", "Peek Recent Actions".

## Docs

- Documentation index: [`docs/README.md`](docs/README.md) — quick links to guides, production readiness, environments, notebooks, and roadmap.

## Unified Features

### From Both Implementations
- **Dual Auth Support**: Choose between Tweepy (OAuth 1.0a) or OAuth 2.0 PKCE
- **Thompson Sampling Learning**: Optimizes topic/time-window choices based on engagement
- **Comprehensive Budget Manager**: Free/Basic/Pro plan support with monthly caps
- **Advanced Rate Limiting**: Per-endpoint tracking, exponential backoff, jitter
- **Time-Window Scheduling**: Morning/afternoon/evening optimal posting times
- **Template-Based Content**: Organized by topics with variation
- **Full Compliance**: Respects X Developer Policy and Automation Rules
- **SQLite Storage**: Actions, metrics, usage tracking, deduplication
- **Dry-Run Mode**: Safe testing without API calls

## Quick Start

> **New here?** See **[docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)** for a complete step-by-step setup guide with screenshots and troubleshooting tips.

### Installation

#### Windows pre-commit /bin/sh warning

> **Note for Windows users:**
> If you see a `/bin/sh` or shell not found error when running pre-commit hooks (e.g., on commit), this is due to pre-commit using a Unix shell by default. You can:
> - Use **Git Bash** as your terminal (recommended for full compatibility)
> - Or, bypass hooks with `git commit --no-verify` (not recommended for regular use)
> See CONTRIBUTING.md for more details.
```powershell
# Windows
.\setup.bat

# Linux/macOS
chmod +x setup.sh && ./setup.sh
```

### Choose Your Auth Method

#### Option 1: Tweepy (OAuth 1.0a) - Simpler Setup
```bash
# Edit .env with OAuth 1.0a credentials
X_AUTH_MODE=tweepy
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
```

#### Option 2: OAuth 2.0 PKCE - Modern, Recommended
```bash
# Edit .env with OAuth 2.0 credentials
X_AUTH_MODE=oauth2
X_CLIENT_ID=your_client_id
X_CLIENT_SECRET=your_client_secret

# Run authorization flow
python src/main.py --authorize
```

### Test and Run
```bash
# Test (dry-run)
python src/main.py --dry-run --mode both

# Go live
python src/main.py --mode both --plan free
```

## Architecture

```
x-agent-unified/
+-- src/
|   +-- auth.py              # Dual auth: Tweepy + OAuth 2.0 PKCE
|   +-- x_client.py          # Unified X API client
|   +-- budget.py            # Budget manager with plan tiers
|   +-- rate_limiter.py      # Rate limit guard
|   +-- storage.py           # SQLite storage
|   +-- scheduler.py         # Time-window scheduler
|   +-- actions.py           # Template-based actions
|   +-- learn.py             # Thompson Sampling learning
|   +-- main.py              # CLI entry point
+-- config.yaml              # Configuration
+-- .env                     # Credentials
+-- README.md
```

### Legacy Code Reference

The `legacy/` directory contains archived planning documents and deprecated configurations from the project's development phases. This includes:

- **`legacy/planning/`** - Sprint planning, analysis, and unification documentation that guided the merge of agent-x and x-agent into the current unified implementation
- **`first-tweet-config.yaml`** - Early minimal configuration (superseded by examples in root)

**All work described in legacy planning docs is complete.** The current production implementation in `src/` includes all planned features (dual auth, learning loop, time-window scheduling, budget management). For migration context and historical perspective, see **[M4_TO_M5_TRANSITION.md](M4_TO_M5_TRANSITION.md)**.

The original agent implementations are preserved in `_archive/` for reference:
- `_archive/agent-x/` - Original Tweepy-based agent with learning loop
- `_archive/x-agent/` - Original OAuth2-based agent with advanced safety

## Authentication Comparison

| Feature | Tweepy (OAuth 1.0a) | OAuth 2.0 PKCE |
|---------|---------------------|----------------|
| Setup | Simpler, 4 tokens | Requires auth flow |
| Scopes | Fixed | Granular control |
| Token Refresh | Manual | Automatic |
| Best For | Quick start, personal | Production, apps |

> **Note**: For live posting, use `X_AUTH_MODE=tweepy`. OAuth 2.0 mode supports read operations and may require additional X Developer App configuration for write access.

### Authentication Mode Examples

```powershell
# Live posting (Tweepy mode)
$env:X_AUTH_MODE = 'tweepy'
python src/main.py --mode post --plan free

# Dry-run testing (OAuth2 recommended)
$env:X_AUTH_MODE = 'oauth2'
python src/main.py --dry-run --mode both
```

## Configuration
### Strategic Notebooks

For ongoing inspection and improvement tracking, see the strategic analysis notebook: [`notebooks/Repo_Inspection_and_DryRun.ipynb`](notebooks/Repo_Inspection_and_DryRun.ipynb).

This notebook contains:
- Latest repository inspection outputs (architecture graph, storage schema snap, config validation)
- Prioritized improvement checklist (modularization, telemetry, rate limiting, security, learning loop)
- Dry-run validation cells for client, scheduler, learning loop, rate limiter
- Metrics & coverage summary (requires prior run of `nox -s test` or `pytest --cov=src --cov-report=xml` to produce `coverage.xml`)

Outside contributors: open it first to understand current state and pick an improvement. If adding new sections, clear outputs before commit (`jupyter nbconvert --clear-output --inplace notebooks/Repo_Inspection_and_DryRun.ipynb`). Promoted checklists should become GitHub Issues (see `docs/roadmap/IMPROVEMENTS.md`).


### Configuration Validation (Optional)

Validate your `config.yaml` before running to catch errors early:

```bash
# Install Pydantic (if not already installed)
pip install pydantic>=2.0

# Validate configuration
python src/main.py --validate config.yaml --dry-run true
```

**Successful validation:**
```
[OK] Configuration validated successfully
```

**Failed validation:**
```
[FAIL] Configuration validation failed:
  - Field 'auth_mode': Value must be 'tweepy' or 'oauth2'
  - Field 'jitter_seconds.min': Must be less than 'max'
```

Common validation errors:
- Invalid `auth_mode` (must be `tweepy` or `oauth2`)
- Invalid `plan` (must be `free`, `basic`, or `pro`)
- Invalid `weekdays` (must be 1-7)
- Invalid `actions` in queries (must be `like`, `reply`, `retweet`)
- `jitter_seconds.min` >= `max`

See **[docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)** for detailed validation examples.

### ASCII policy

All Python source code under `src/` is maintained as ASCII-only to avoid Windows console encoding issues and simplify tooling. By default, the ASCII scanner checks `src/` only. Documentation may use limited Unicode for readability — include `docs/` explicitly if you want to scan docs too:

```powershell
# Code only
python scripts/check_ascii.py --scan-dirs src

# Code + docs
python scripts/check_ascii.py --scan-dirs src docs
```

To enforce ASCII-only everywhere (including docs) in CI, adjust the workflow to include `docs/` as needed.

### Configuration Schema

```yaml
# Auth mode
auth_mode: tweepy  # or oauth2

# Plan tier
plan: free  # free, basic, pro

# Topics for content
topics:
  - power-platform
  - data-viz
  - automation

# Queries for interaction
queries:
  - query: '(Power BI OR "Power Platform") lang:en -is:retweet -is:reply'
    actions: [like, reply]

# Time windows
windows:
  enabled: true
  times:
    morning: [9, 12]
    afternoon: [13, 17]
    evening: [18, 21]

# Learning loop
learning:
  enabled: true
  algorithm: thompson_sampling
```

## Thompson Sampling Learning

The agent learns which topic x time-window x media combinations perform best:

```bash
# Settle metrics for a post (manual)
python src/main.py --settle POST_ID --arm "power-platform|morning|false"

# Settle all posts automatically
python src/main.py --settle-all
```

**How it works:**
1. Creates posts with different topic/time/media combinations
2. Tracks engagement (likes, replies, retweets)
3. Computes reward score (0-1)
4. Updates Beta distribution for each "arm"
5. Biases future choices toward high-performing combinations

## Budget and Rate Limits

### Monthly Caps by Plan
| Plan | Reads | Writes | Notes |
|------|-------|--------|-------|
| Free | 100 | 500 | Start here |
| Basic | 15,000 | 50,000 | For active use |
| Pro | 1,000,000 | 300,000 | High volume |

### Check Status
```bash
# View budget usage
python src/main.py --safety print-budget

# View rate limits
python src/main.py --safety print-limits
```

## Usage Examples

### Post Mode (Time-Window Aware)
```bash
# Post using optimal time window
python src/main.py --mode post --plan free
```

### Interact Mode
```bash
# Search, like, reply based on queries
python src/main.py --mode interact --plan free
```

### Both Modes
```bash
# Post AND interact
python src/main.py --mode both --plan free
```

### Learning Loop
```bash
# Settle metrics after 24 hours
python src/main.py --settle-all
```

## CLI Reference

```bash
# Main modes
python src/main.py --mode [post|interact|both]

# Auth
python src/main.py --authorize              # OAuth 2.0 only

# Dry run
python src/main.py --dry-run --mode both

# Plan tier
python src/main.py --plan [free|basic|pro]

# Safety commands
python src/main.py --safety [print-budget|print-limits]

# Learning
python src/main.py --settle POST_ID --arm "topic|window|media"
python src/main.py --settle-all
```

## Migration from Old Agents

### From agent-x (Tweepy)
1. Copy `.env` credentials
2. Set `auth_mode: tweepy` in config
3. Run normally - all features preserved + new ones added

### From x-agent (OAuth 2.0)
1. Keep `.token.json` file
2. Set `auth_mode: oauth2` in config
3. Run normally - all features preserved + learning added

## Testing

```bash
# Smoke tests (dry-run)
python tests/smoke_test.py

# Live test (creates ONE post)
python tests/live_test.py --confirm

# Learning test
python tests/test_learning.py
```

## Local Development Tips

Type checking (parity with CI):

```bash
# macOS/Linux
./scripts/mypy.sh

# Windows PowerShell
./scripts/mypy.ps1
```

Nox sessions (optional, unified tasks):

```bash
# Lint, type-check, and test via nox
nox -s lint
nox -s type
nox -s test
nox -s all  # runs all three in sequence
```

## Telemetry (Optional)
### Secrets & GitHub Environments

Scripts `scripts/gh_env_setup.sh` / `scripts/gh_env_setup.ps1` help bootstrap staging/production GitHub Environments and set required secrets safely. Place X API and OAuth2 credentials in environment secrets (or override via `config.yaml` locally). **Do not commit secrets** (`.env`, `.token.json` are git‑ignored). Full walkthrough: [`docs/ENVIRONMENTS.md`](docs/ENVIRONMENTS.md).


The agent can emit OpenTelemetry traces and include W3C TraceContext IDs in logs. See [docs/telemetry.md](docs/telemetry.md) for full instructions.

- Enable tracing by setting an environment variable:

  ```powershell
  # Windows PowerShell (canonical)
  $env:TELEMETRY_ENABLED = "true"
  # Backward-compatible: $env:ENABLE_TELEMETRY = "true"
  ```

  ```bash
  # macOS/Linux (canonical)
  export TELEMETRY_ENABLED=true
  # Backward-compatible: export ENABLE_TELEMETRY=true
  ```

- Optional configuration:
  - `OTEL_SERVICE_NAME` (default: `x-agent`)
  - `OTEL_EXPORTER_OTLP_ENDPOINT` e.g. `http://localhost:4318/v1/traces` (for OTLP/HTTP)
  - `OTEL_TRACES_SAMPLER` values:
    - `always_on`
    - `parentbased_traceidratio/<ratio>` (e.g. `parentbased_traceidratio/0.2`)

When enabled, logs include `[trace_id=... span_id=...]` for any active span. If OpenTelemetry is not
installed, the agent falls back to a no-op tracer automatically.

## Key Improvements

### Over agent-x
- [x] OAuth 2.0 PKCE support (optional)
- [x] Better budget manager with plan tiers
- [x] More comprehensive rate limiting
- [x] Improved documentation
- [x] Better error handling

### Over x-agent
- [x] Tweepy support for simpler auth
- [x] Thompson Sampling learning loop
- [x] Time-window scheduling
- [x] Template-based content
- [x] Simpler onboarding option

## Reliability

This project includes a small reliability layer that hardens OAuth2 (raw HTTP) calls while
keeping Tweepy-based flows unchanged. Key points:

- Timeouts: all raw HTTP calls use an explicit default timeout (DEFAULT_TIMEOUT = 10s) for
  connect/read to avoid hanging network calls.
- Retries: bounded retries are performed with exponential backoff and jitter. Retryable
  statuses are 429 and 500-504.
- Rate-limit handling: when a 429 response includes an `x-rate-limit-reset` header, the
  client will wait until the reset time (capped) before retrying to be polite to the API.
- Idempotency: POST requests automatically include a deterministic `Idempotency-Key`
  derived from the JSON payload (sha256 of canonical JSON). GET and DELETE are not
  automatically idempotent by header.

Rationale: these changes make OAuth2 network interactions safer and more policy-compliant
under transient failures and rate limits. Dry-run behavior is unchanged; Tweepy mode is
untouched and continues to rely on its own retry logic.

## Best Practices

### For Free Plan
```yaml
plan: free
windows:
  enabled: true
max_per_window:
  post: 1
  like: 5
  reply: 2
learning:
  enabled: true
```

### For Basic/Pro Plans
```yaml
plan: basic  # or pro
windows:
  enabled: false  # More flexibility
max_per_window:
  post: 5
  like: 20
  reply: 10
learning:
  enabled: true
```

## Documentation

- **README.md** - This file (overview)
- **[docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md)** - 5-minute setup guide
- **[docs/telemetry.md](docs/telemetry.md)** - Observability and tracing
- **[docs/guides/](docs/guides/)** - Additional guides (first tweet, read budget, migration)

## Developer Setup

### Pre-commit Hooks (Recommended)

Install pre-commit hooks to ensure code quality before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The hooks will automatically:
- ✅ Run `ruff` linter and formatter
- ✅ Validate config schema tests
- ✅ Scan for non-ASCII characters
- ✅ Check YAML/TOML/JSON syntax
- ✅ Fix trailing whitespace and line endings

**Performance Note**: Only fast config tests run on commit (not the full test suite).

### Running Tests

```bash
# Quick test run
pytest -q

# Verbose output
pytest -v

# With coverage
pytest --cov=src --cov-report=term

# Specific test file
pytest tests/test_config_schema.py -v
```

### Type Checking

```bash
# Windows
.\scripts\mypy.ps1

# Linux/macOS
./scripts/mypy.sh

# Or use nox
nox -s type
```

### Validation Scripts

```bash
# Verify telemetry in dry-run mode
python scripts/verify_telemetry_dry_run.py

# Check ASCII compliance
python scripts/check_ascii.py --scan-dirs src docs
```

## Compliance

- [x] Only official X API (v2 + v1.1 media)
- [x] Both auth methods supported
- [x] Respects all rate limits
- [x] Enforces plan caps
- [x] Full audit logging
- [x] Deduplication
- [x] Follows X Developer Policy

## Repository Structure

```
Play-stuff/
├── src/                        # Core agent source code
│   ├── main.py                # CLI entry point
│   ├── x_client.py            # Unified X API client (Tweepy + OAuth2)
│   ├── auth.py                # Dual authentication (OAuth 1.0a + PKCE)
│   ├── scheduler.py           # Time-window orchestration
│   ├── actions.py             # Content generation & posting
│   ├── budget.py              # Plan caps & safety buffers
│   ├── rate_limiter.py        # Per-endpoint rate limiting
│   ├── storage.py             # SQLite persistence & deduplication
│   ├── learn.py               # Thompson Sampling bandit
│   ├── telemetry.py           # OpenTelemetry tracing
│   └── reliability.py         # Retry logic with backoff
│
├── tests/                      # Test suite (97.8% coverage)
│   ├── test_x_client.py       # Client behavior verification
│   ├── test_auth.py           # Authentication flows
│   ├── test_budget.py         # Plan enforcement
│   ├── test_rate_limiter.py   # Rate limit tracking
│   ├── test_storage.py        # Database operations
│   ├── test_telemetry*.py     # Tracing & observability
│   └── conftest.py            # Shared fixtures
│
├── docs/                       # Production documentation
│   ├── guides/                # User-facing guides
│   │   ├── QUICKSTART.md      # Getting started
│   │   ├── FIRST_TWEET_GUIDE.md
│   │   └── READ_BUDGET.md     # Plan cap documentation
│   ├── observability/         # Production monitoring
│   │   ├── otel-jaeger-setup.md    # OpenTelemetry + Jaeger
│   │   └── alerting-checklist.md   # Prometheus alerts
│   └── TROUBLESHOOTING_403.md # Auth debugging
│
├── legacy/                     # Historical documentation
│   ├── planning/              # Sprint & milestone reports
│   │   ├── PHASE_*.md         # Development phases
│   │   ├── COVERAGE_*.md      # Coverage campaigns
│   │   └── SPRINT_*.md        # Agile planning docs
│   └── *.yaml                 # Old config variants
│
├── _archive/                   # Pre-unification implementations
│   ├── agent-x/               # Original Tweepy agent
│   └── x-agent/               # Original OAuth2 agent
│
├── data/                       # Runtime data directory
│   └── agent_unified.db       # SQLite database (gitignored)
│
├── scripts/                    # Development tools
│   ├── mypy.ps1 / mypy.sh     # Type checking
│   └── verify_telemetry*.py   # Validation scripts
│
└── config.yaml                 # Active runtime configuration
```

**Key Files**:
- `config.yaml`: Active agent configuration (see `config.example.yaml` for template)
- `config.safe-first-run.yaml`: Safe production starter (16 actions/day)
- `.env`: API keys and secrets (create from `.env.example`)
- `pyproject.toml`: Python dependencies & project metadata
- `pytest.ini`: Test configuration with 97.7% coverage gate

**Documentation Hierarchy**:
- **docs/guides/**: User-facing quickstarts and tutorials
- **docs/observability/**: Production monitoring setup (OTEL, Prometheus, Jaeger)
- **legacy/planning/**: Historical sprint reports and coverage campaigns
- **_archive/**: Pre-unification agent implementations (reference only)

## Contributing

This unified agent combines:

- **agent-x**: Tweepy-based with learning loop
- **x-agent**: OAuth 2.0 with comprehensive safety

Both implementations are preserved in archive/ for reference.

**Development Workflow**:
1. Fork and clone the repository
2. Run `./setup.bat` (Windows) or `./setup.sh` (Linux/macOS)
3. Install pre-commit hooks: `pip install pre-commit && pre-commit install`
4. Make your changes and ensure tests pass: `pytest -q`
5. Submit a pull request

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines, CI expectations, and troubleshooting tips.

## Troubleshooting

### Common Pre-commit Hook Errors

**Error: `/bin/sh: not found`** (Windows)
- **Cause**: Pre-commit expects a Unix shell
- **Fix**: Use Git Bash as your terminal, or bypass with `git commit --no-verify` (not recommended)

**Error: `mypy` fails on Windows paths**
- **Cause**: Path separator differences
- **Fix**: Run `./scripts/mypy.ps1` which normalizes paths for Windows

**Error: `ruff` import sorting conflicts**
- **Cause**: Manual import ordering doesn't match ruff's rules
- **Fix**: Run `ruff check . --fix` to auto-fix import order

### Windows Workflow Tips

- **Use Git Bash** for full compatibility with pre-commit hooks
- **Or use WSL** for a native Linux environment
- **PowerShell users**: Bypass hooks with `--no-verify` or install Git Bash
- **Line endings**: Repo is configured for CRLF on Windows (handled by `.gitattributes`)

### CI Coverage Artifacts

Coverage reports are uploaded to:
- **Codecov**: [View coverage trends](https://codecov.io/gh/georgicaradu5-source/Play-stuff)
- **CI artifacts**: Download `coverage-report` or `coverage-report-telemetry-extras` from any CI run (30-day retention)

Current coverage: **97.8%** (quality gate: 97.7% enforced in `pytest.ini`)

## License

MIT License - See LICENSE file

---

**Choose your auth, keep your budget, learn what works. Simple.**
