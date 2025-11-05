# First Tweet Guide

Detailed walkthrough for creating your first automated tweet with X Agent Unified.

> **⚡ Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for initial setup. This guide assumes you've completed Steps 1-4.

## Overview

This guide walks you through creating your first automated tweet safely, including:

1. Pre-flight validation
2. Dry-run testing
3. Live execution
4. Post-tweet verification
5. Engagement tracking

**Estimated time**: 10-15 minutes

## Prerequisites Checklist

Before your first tweet, ensure:

- ✅ Python environment activated (`.venv/Scripts/activate` or `source .venv/bin/activate`)
- ✅ `.env` file created with credentials
- ✅ `config.yaml` configured with topics and windows
- ✅ Database directory exists (`data/`)
- ✅ Authentication tested (dry-run completed successfully)

## Step 1: Pre-Flight Validation

Run validation checks to ensure everything is configured correctly:

```bash
# Check code quality
make lint

# Verify types
make type

# Run unit tests (should see 18 passed, 2 skipped)
make test
```

**Expected output:**
```
==================== 18 passed, 2 skipped ====================
```

If any tests fail, fix issues before proceeding.

## Step 2: Dry-Run Test

Test the agent without creating real tweets:

```bash
# Dry-run in post mode only
python src/main.py --dry-run true --mode post --plan free
```

**Expected output:**
```
[INFO] X Agent starting in post mode (dry-run: True)
[INFO] Auth mode: tweepy
[INFO] Plan: free (50 tweets/day, 1500 tweets/month)
[INFO] Current time window: morning (9:00-12:00)
[DRY-RUN] Would create post: "Just discovered a cool trick with Power BI dashboards! 📊 #PowerBI #DataViz"
[DRY-RUN] Would log action to database: kind=post, arm=power-platform|morning|false
[INFO] Cycle complete. No errors.
```

**Verify database behavior:**
```bash
# Should show NO actions (dry-run doesn't write)
python scripts/peek_actions.py --limit 10
```

**Expected**: Empty table or "No actions found"

### Common Dry-Run Issues

**Issue**: "No window active"  
**Fix**: Check current time matches configured windows in `config.yaml`. Test with `windows: [morning, afternoon, evening]` to cover all day.

**Issue**: "Budget exceeded"  
**Fix**: Database has old data. Delete `data/agent_unified.db` and rerun setup.

**Issue**: "Authentication failed"  
**Fix**: Verify `.env` credentials. For Tweepy, ensure all 4 tokens are correct. For OAuth2, rerun `--authorize`.

## Step 3: Prepare for Live Execution

Before going live, review your configuration:

### Review Topics

Edit `config.yaml`:
```yaml
topics:
  - power-platform  # Will generate tweets about Power Platform
  - data-viz        # Will generate tweets about data visualization
  # Remove or add topics as needed
```

### Review Time Windows

Ensure at least one window covers current time:
```yaml
schedule:
  windows:
    - morning    # 9am-12pm
    - afternoon  # 1pm-5pm
    - evening    # 6pm-9pm
```

**Check current time window:**
```bash
# Run dry-run and look for "Current time window: X" in output
python src/main.py --dry-run true --mode post
```

### Set Conservative Limits

For first run, use minimal limits:
```yaml
max_per_window:
  post: 1      # ONE tweet per window
  reply: 0     # Disable replies
  like: 0      # Disable likes
  follow: 0    # Disable follows
```

## Step 4: Create Your First Tweet (Live)

> ⚠️ **WARNING**: This will create a REAL tweet on your X account. Ensure you're logged into the correct account.

```bash
# Post mode only, free plan
python src/main.py --mode post --plan free
```

**Expected output:**
```
[INFO] X Agent starting in post mode (dry-run: False)
[INFO] Auth mode: tweepy
[INFO] Plan: free
[INFO] Current time window: morning
[INFO] Creating post with template...
[INFO] ✅ Post created: Tweet ID 1234567890123456789
[INFO] Logged action: post (arm: power-platform|morning|false)
[INFO] Cycle complete.
```

**Look for**:
- ✅ "Post created: Tweet ID XXXXX" — Success!
- ✅ "Logged action" — Database updated
- ❌ Any ERROR messages — Check authentication/rate limits

## Step 5: Verify Tweet Creation

### Check on X.com

1. Open [twitter.com](https://twitter.com) (or X.com)
2. Go to your profile
3. Verify new tweet appears

### Check Database

```bash
# View recent actions
python scripts/peek_actions.py --limit 5 --kind post
```

**Expected output:**
```
| action_id | kind | tweet_id          | text                          | timestamp           |
|-----------|------|-------------------|-------------------------------|---------------------|
| 1         | post | 1234567890123... | Just discovered a cool tri... | 2025-11-06 10:30:15 |
```

### Check Budget Usage

```bash
# Print budget status
python src/main.py --safety print-budget
```

**Expected output:**
```
Plan: free
Monthly Caps:
  - Tweets: 1 / 1,500 (0.07%)
  - Reads: 0 / 100,000 (0.00%)
...
```

## Step 6: Monitor & Learn

### Track Engagement (After 24-48 Hours)

Wait 24-48 hours for engagement metrics to stabilize, then run:

```bash
# Settle metrics for all posts
python src/main.py --settle-all
```

**What this does:**
- Fetches likes, replies, retweets for each tweet
- Calculates reward score based on engagement
- Updates Thompson Sampling bandit
- Future tweets favor high-performing topic/window/media combinations

### View Learning Progress

Check bandit state in database:
```bash
# Connect to database
sqlite3 data/agent_unified.db

# Query bandit table
SELECT arm, alpha, beta FROM bandit ORDER BY (alpha / (alpha + beta)) DESC LIMIT 10;
```

**Interpretation:**
- Higher `alpha / (alpha + beta)` = better performance
- Agent will choose these arms more often

## Troubleshooting

### Tweet Not Created

**Check 1: Time Window**
```bash
# Verify current time is within a configured window
python src/main.py --dry-run true --mode post
# Look for "Current time window: X" or "No window active"
```

**Fix**: Adjust `schedule.windows` or wait for next window.

**Check 2: Weekday**
```yaml
# In config.yaml
cadence:
  weekdays: [1, 2, 3, 4, 5]  # 1=Mon, 7=Sun
```

**Fix**: Add current weekday number to list.

**Check 3: Budget**
```bash
python src/main.py --safety print-budget
```

**Fix**: If exceeded, wait until next month or increase plan tier.

### Authentication Error

**Tweepy Mode:**
```bash
# Test credentials
python -c "import tweepy; client = tweepy.Client(bearer_token='YOUR_BEARER_TOKEN'); print(client.get_me())"
```

**OAuth2 Mode:**
```bash
# Reauthorize
python src/main.py --authorize
```

### Duplicate Content Error

Agent has built-in deduplication. If you see "Duplicate content detected":

**Fix**: Wait 7 days (default dedup window) or adjust templates in `src/actions.py`.

### Rate Limit Error

Agent automatically handles rate limits with exponential backoff.

**Check current limits:**
```bash
python src/main.py --safety print-limits
```

**Fix**: Reduce `max_per_window` values or wait for limit reset.

## Next Steps

### Enable Interaction Mode

After successful posting, enable interactions:

```yaml
# In config.yaml
max_per_window:
  post: 1
  like: 5      # Enable likes
  reply: 2     # Enable replies
```

```bash
# Run both modes
python src/main.py --mode both --plan free
```

### Schedule Regular Runs

**Option 1: Windows Task Scheduler**
```powershell
# Create scheduled task (Windows)
schtasks /create /tn "X Agent" /tr "C:\path\to\Play-stuff\.venv\Scripts\python.exe C:\path\to\Play-stuff\src\main.py --mode both --plan free" /sc daily /st 10:00
```

**Option 2: Cron (Linux/macOS)**
```bash
# Add to crontab
crontab -e

# Run every 3 hours
0 */3 * * * cd /path/to/Play-stuff && .venv/bin/python src/main.py --mode both --plan free >> logs/agent.log 2>&1
```

**Option 3: Manual Runs**

Run manually during each time window (morning, afternoon, evening).

### Optimize with Learning

After 1-2 weeks of regular posting:

1. Run `--settle-all` daily
2. Review bandit performance
3. Adjust topics based on what's working
4. Experiment with different windows

### Scale Up

Once comfortable:

- Increase `max_per_window` limits
- Add more topics
- Add more search queries for interaction
- Consider upgrading to basic/pro plan

## Checklist Summary

**Before First Tweet:**
- [ ] Validation passed (`make lint`, `make type`, `make test`)
- [ ] Dry-run successful (no errors)
- [ ] Database empty or clean
- [ ] Time window active
- [ ] Weekday configured
- [ ] Budget available

**After First Tweet:**
- [ ] Tweet visible on X.com
- [ ] Database updated (`peek_actions.py` shows tweet)
- [ ] No error messages
- [ ] Budget decremented correctly

**Within 48 Hours:**
- [ ] Run `--settle-all` to fetch metrics
- [ ] Review engagement
- [ ] Adjust config if needed

**Congratulations!** You've successfully deployed an autonomous X agent. 🎉

## Further Reading

- [READ_BUDGET.md](READ_BUDGET.md) — Understanding budget management
- [ENVIRONMENTS.md](../ENVIRONMENTS.md) — GitHub Environments setup
- [../../docs/telemetry.md](../../docs/telemetry.md) — Enabling observability
- [../../README.md](../../README.md) — Full feature documentation
