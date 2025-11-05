# Free Mode Operations Guide

## Overview

Free plan operation provides safe, dry-run automation without consuming write quotas. This mode is perfect for testing, learning, and monitoring system behavior.

## Key Characteristics

### Plan Limits
- **Reads**: 0/100 per month (dry-run doesn't consume)
- **Writes**: 0/500 per month (dry-run mode only)
- **Media**: Not available in free mode

### Default Behavior
- **No writes by default**: All operations run in dry-run mode
- **Safe testing**: Full system validation without API consumption
- **Budget monitoring**: Track hypothetical usage

## Recommended Commands

### Standard Dry-Run Operation
```powershell
# Both posting and engagement simulation
python src/main.py --dry-run --mode both

# OAuth2 mode (recommended for dry-runs)
$env:X_AUTH_MODE = 'oauth2'
python src/main.py --dry-run --mode both
```

### Safety Monitoring
```powershell
# Check budget status
python src/main.py --safety print-budget

# Check rate limits  
python src/main.py --safety print-limits

# View recent actions
python -c "import sqlite3; conn = sqlite3.connect('data/agent_unified.db'); conn.row_factory = sqlite3.Row; rows = conn.execute('SELECT * FROM actions ORDER BY dt DESC LIMIT 5').fetchall(); print('\n'.join(str(dict(row)) for row in rows))"
```

## Recommended Cadence

### Manual Testing
- **Daily**: Run dry-run operations to validate system health
- **Before changes**: Test configuration updates safely
- **Monitoring**: Check budget and rate limit status

### Automated Schedule
- **Morning Check (09:00 UTC)**: System health validation
- **Evening Check (17:00 UTC)**: Daily summary and metrics

## Artifacts Location

### Generated Files
- **Logs**: `artifacts/dryrun-YYYY-MM-DD-HHMM/`
- **Database snapshots**: `db-tail.json`
- **Safety outputs**: `budget-status.txt`, `rate-limits.txt`
- **Summary reports**: `dryrun-summary.txt`

### Gitignore Status
All artifacts are automatically excluded from version control via `.gitignore`.

## Automation Workflows

### Scheduled Dry-Run (CI)
- **Workflow**: `.github/workflows/ci-free-mode-dryrun.yml`
- **Schedule**: 09:00 and 17:00 UTC daily
- **Environment**: staging (OAuth2 mode)
- **Outputs**: Logs, safety reports, database tail

### Manual Triggers
Available through GitHub Actions interface for immediate testing.

## Safety Features

### Built-in Protections
- **Duplicate detection**: Prevents repeat content
- **Rate limit respect**: Honors X API limits even in dry-run
- **Budget tracking**: Monitors hypothetical usage
- **Comprehensive logging**: Full audit trail

### Monitoring Points
- Database growth and action history
- Authentication token validity
- Configuration file integrity
- Workflow execution success

## Transition to Paid Plans

When ready to move beyond free mode:

1. **Upgrade plan**: Update budget configuration
2. **Enable live mode**: Remove `--dry-run` flag
3. **Switch authentication**: Use `X_AUTH_MODE=tweepy` for writes
4. **Monitor usage**: Track actual API consumption

See `docs/BUDGET.md` for plan details and upgrade procedures.