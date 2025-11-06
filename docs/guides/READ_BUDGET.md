# Budget Management Guide

Complete guide to understanding and managing budget limits in X Agent Unified.

> **[TARGET] Quick Reference**: Run `python src/main.py --safety print-budget` to see current usage.

## Overview

X Agent Unified enforces budget limits to:
- [OK] Prevent exceeding X API rate limits
- [OK] Avoid unexpected costs on paid X plans
- [OK] Ensure sustainable, policy-compliant automation
- [OK] Protect against runaway automation bugs

Budget limits apply at **two levels**:
1. **Monthly Caps**  -  Total actions per month (resets monthly)
2. **Daily Caps**  -  Maximum actions per day (resets daily)

## Budget Plan Tiers

### Free Plan (Default)

**Best for**: Testing, personal accounts, low-volume automation

**Monthly Limits**:
- **Reads**: 100,000/month (searches, profile lookups)
- **Writes**: 1,500/month (tweets, likes, follows, replies)

**Daily Limits**:
- **Tweets**: 50/day
- **Likes**: ~50/day (derived from monthly)
- **Follows**: ~50/day

**Cost**: $0 (X Developer Free tier)

**Usage**:
```yaml
# In config.yaml
plan: free
```

```bash
# Or via CLI
python src/main.py --mode both --plan free
```

### Basic Plan

**Best for**: Active personal accounts, moderate automation

**Monthly Limits**:
- **Reads**: 1,000,000/month
- **Writes**: 50,000/month

**Daily Limits**:
- **Tweets**: 100/day
- **Likes**: ~1,600/day
- **Follows**: ~1,600/day

**Cost**: ~$100/month (X Basic tier, check current pricing)

**Usage**:
```yaml
plan: basic
```

### Pro Plan

**Best for**: Business accounts, high-volume automation, agencies

**Monthly Limits**:
- **Reads**: 10,000,000/month
- **Writes**: 300,000/month

**Daily Limits**:
- **Tweets**: 300/day
- **Likes**: ~10,000/day
- **Follows**: ~10,000/day

**Cost**: ~$5,000/month (X Pro tier, check current pricing)

**Usage**:
```yaml
plan: pro
```

## How Budget Enforcement Works

### 1. Database Tracking

All actions are logged to `data/agent_unified.db`:

```sql
-- actions table
CREATE TABLE actions (
    action_id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,  -- 'post', 'like', 'reply', 'follow', 'repost'
    timestamp TEXT NOT NULL,
    tweet_id TEXT,
    text TEXT
);

-- monthly_usage table (aggregated)
CREATE TABLE monthly_usage (
    month TEXT PRIMARY KEY,
    post_count INTEGER,
    like_count INTEGER,
    reply_count INTEGER,
    follow_count INTEGER,
    repost_count INTEGER
);
```

### 2. Pre-Action Checks

Before every action, `budget.py` checks:

```python
# Pseudocode
if storage.get_monthly_usage('post') >= plan_monthly_cap['post']:
    raise BudgetExceededError("Monthly tweet limit reached")

if storage.get_daily_usage('post') >= plan_daily_cap['post']:
    raise BudgetExceededError("Daily tweet limit reached")

# If checks pass, proceed with action
```

### 3. Safety Buffers

By default, agent applies a **5% safety buffer** to avoid hitting exact limits:

```yaml
# In budget.py (configurable)
safety_buffer: 0.05  # 5%

# Example: Free plan has 1,500 tweets/month
# Effective limit: 1,500 * 0.95 = 1,425 tweets
```

**Why**: Prevents edge cases where timing causes slight overages.

## Checking Budget Status

### Command Line

```bash
# Print current budget usage
python src/main.py --safety print-budget
```

**Output**:
```
=======================================
           BUDGET STATUS
=======================================

Plan: free

Monthly Caps (November 2025):
  Reads:  1,234 / 100,000 (1.23%) [OK]
  Writes:   42 / 1,500 (2.80%) [OK]

Daily Caps (2025-11-06):
  Tweets:  3 / 50 (6.00%) [OK]
  Likes:   15 / 50 (30.00%) [OK]
  Replies: 2 / 50 (4.00%) [OK]
  Follows: 1 / 50 (2.00%) [OK]

Safety Buffer: 5%

Status: [GREEN] HEALTHY
Next Reset: 2025-12-01 (24 days)
```

### Via Database Query

```bash
# Direct database query
sqlite3 data/agent_unified.db "SELECT * FROM monthly_usage WHERE month='2025-11';"
```

**Output**:
```
2025-11|3|15|2|1|0
(month | post_count | like_count | reply_count | follow_count | repost_count)
```

### Via Python Script

```bash
# Use peek_actions.py for recent actions
python scripts/peek_actions.py --limit 20
```

## Rate Limits vs Budget Limits

**Budget Limits** (this guide):
- Enforced by **agent** locally
- Monthly/daily caps based on your X plan tier
- Prevents exceeding subscription limits

**Rate Limits** (separate system):
- Enforced by **X API**
- Per-endpoint, short time windows (15 min, 24 hours)
- Example: 180 search requests per 15 minutes

**Both work together**:
1. Budget check (local) -> passes
2. Rate limit check (local tracking) -> passes
3. API call -> X enforces server-side rate limits

Check rate limits:
```bash
python src/main.py --safety print-limits
```

## Managing Budget

### Strategy 1: Adjust Per-Window Limits

Control how many actions happen in each time window:

```yaml
# Conservative (free plan)
max_per_window:
  post: 1      # 3/day (3 windows) = 90/month
  like: 5      # 15/day = 450/month
  reply: 2     # 6/day = 180/month
  follow: 1    # 3/day = 90/month

# Total writes: ~810/month (well under 1,500)
```

```yaml
# Aggressive (basic plan)
max_per_window:
  post: 5      # 15/day = 450/month
  like: 20     # 60/day = 1,800/month
  reply: 10    # 30/day = 900/month
  follow: 5    # 15/day = 450/month

# Total writes: ~3,600/month (under 50,000)
```

### Strategy 2: Disable Weekends

Reduce monthly usage by posting only weekdays:

```yaml
cadence:
  weekdays: [1, 2, 3, 4, 5]  # Mon-Fri only

# Effect: Reduces monthly actions by ~28% (5/7 days)
```

### Strategy 3: Reduce Time Windows

Post less frequently by using fewer windows:

```yaml
# Only post in morning
schedule:
  windows:
    - morning

# Effect: 1/3 the daily actions
```

### Strategy 4: Monitor & Adjust

Weekly monitoring workflow:

```bash
# 1. Check budget (every Monday)
python src/main.py --safety print-budget

# 2. If approaching limits (>70%), reduce per-window limits
# Edit config.yaml and decrease max_per_window values

# 3. If under-utilizing (<30%), increase limits
# Edit config.yaml and increase max_per_window values

# 4. Test changes
python src/main.py --dry-run true --mode both
```

## Budget Exceeded Scenarios

### Scenario 1: Monthly Limit Reached

**Symptom**: Agent stops posting, logs "Monthly budget exceeded"

**Solutions**:
1. **Wait**: Limits reset on 1st of next month
2. **Upgrade Plan**: Switch to basic/pro tier
3. **Delete Old Data**: Clear database (loses historical metrics)
   ```bash
   rm data/agent_unified.db
   python setup.bat  # Recreates database
   ```

### Scenario 2: Daily Limit Reached

**Symptom**: Agent stops posting for rest of day

**Solutions**:
1. **Wait**: Limits reset at midnight UTC
2. **Reduce Actions**: Lower `max_per_window` for future days
3. **Check for Bugs**: Ensure agent isn't running multiple times

### Scenario 3: Unexpected High Usage

**Symptom**: Budget consumed faster than expected

**Diagnosis**:
```bash
# 1. Check recent actions
python scripts/peek_actions.py --limit 50

# 2. Look for duplicate runs or errors causing retries
grep ERROR logs/*.log  # If you're logging to files

# 3. Check if agent is running multiple instances
ps aux | grep python  # (Linux/macOS)
Get-Process | Where-Object {$_.ProcessName -like "*python*"}  # (Windows)
```

**Fix**: Kill duplicate processes, adjust config, add monitoring

## Best Practices

### For Free Plan Users

[OK] **Do**:
- Use time windows to space out actions
- Enable learning loop to optimize performance
- Monitor weekly and adjust limits proactively
- Use dry-run mode extensively for testing

[X] **Don't**:
- Run agent more than 3x per day (once per window)
- Enable all action types (pick 2-3)
- Ignore budget warnings

### For Basic/Pro Plan Users

[OK] **Do**:
- Increase limits gradually (test with 2x, then 5x)
- Use multiple time windows for natural patterns
- Enable all interaction modes if desired
- Set up monitoring/alerting for budget thresholds

[X] **Don't**:
- Max out limits immediately (ramp up over weeks)
- Ignore rate limits (budget != rate limits)
- Forget to run `--settle-all` for learning optimization

### General Best Practices

1. **Start Conservative**: Begin with low limits, increase as you monitor
2. **Monitor Weekly**: Check budget every Monday
3. **Automate Safely**: Use scheduled tasks with monitoring
4. **Budget for Errors**: Retries consume budget; plan for ~10% overhead
5. **Track Performance**: Use `--settle-all` to ensure budget is well-spent

## Advanced: Customizing Budget Rules

For custom plan tiers or different budget logic, edit `src/budget.py`:

```python
# src/budget.py
PLAN_CAPS = {
    "free": {
        "monthly": {"read": 100_000, "write": 1_500},
        "daily": {"tweet": 50, "like": 50, "follow": 50},
    },
    "custom": {  # Add your own
        "monthly": {"read": 500_000, "write": 10_000},
        "daily": {"tweet": 200, "like": 200, "follow": 200},
    },
}
```

Then use in config:
```yaml
plan: custom
```

## Troubleshooting

### Budget Not Updating

**Check database**:
```bash
sqlite3 data/agent_unified.db "SELECT * FROM actions ORDER BY action_id DESC LIMIT 5;"
```

**If empty**: Actions aren't being logged. Check for errors in console.

### Budget Shows Wrong Month

**Check system time**:
```bash
date  # (Linux/macOS)
Get-Date  # (Windows PowerShell)
```

**If wrong**: Fix system clock. Budget uses current month for tracking.

### Budget Reset Not Working

Budget resets are automatic based on date. If not resetting:

1. **Check code**: `src/storage.py` -> `get_monthly_usage()` should use current month
2. **Manual reset**: Delete old month from database
   ```bash
   sqlite3 data/agent_unified.db "DELETE FROM monthly_usage WHERE month='2025-10';"
   ```

## Summary

**Key Takeaways**:
- Budget limits protect against overages and ensure policy compliance
- Three tiers: free (1.5K/month), basic (50K/month), pro (300K/month)
- Check status anytime: `python src/main.py --safety print-budget`
- Adjust limits in `config.yaml` -> `max_per_window`
- Monitor weekly, adjust proactively

**Quick Commands**:
```bash
# Check budget
python src/main.py --safety print-budget

# Check rate limits
python src/main.py --safety print-limits

# View recent actions
python scripts/peek_actions.py --limit 20

# Test config changes (dry-run)
python src/main.py --dry-run true --mode both
```

For questions, see [QUICKSTART.md](QUICKSTART.md) or open a [GitHub Issue](https://github.com/georgicaradu5-source/Play-stuff/issues).
