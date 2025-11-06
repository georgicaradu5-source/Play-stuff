# First Tweet Steps  -  Quick Checklist

Minimal checklist for creating your first tweet. See [FIRST_TWEET_GUIDE.md](FIRST_TWEET_GUIDE.md) for detailed explanations.

## [OK] Pre-Flight (5 min)

```bash
# 1. Activate environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Run validation
make lint && make type && make test

# 3. Verify .env exists with credentials
cat .env  # (or type .env on Windows)
```

**Expected**: All tests pass (18 passed, 2 skipped)

## [OK] Dry-Run Test (2 min)

```bash
# Test without creating real tweets
python src/main.py --dry-run true --mode post --plan free
```

**Expected**: `[DRY-RUN] Would create post: ...`
**No errors**: [OK] Continue | **Errors**: Fix before proceeding

## [OK] Configure Limits (1 min)

Edit `config.yaml`:

```yaml
max_per_window:
  post: 1      # ONE tweet only
  reply: 0     # Disable
  like: 0      # Disable
  follow: 0    # Disable
```

**Save file**

## [OK] Check Time Window (1 min)

```bash
# Verify current time is in a window
python src/main.py --dry-run true --mode post | grep "window"
```

**Expected**: `Current time window: morning` (or afternoon/evening)
**If "No window active"**: Wait or adjust `schedule.windows` in config

## [OK] Create First Tweet (1 min)

> [WARN] **LIVE MODE**  -  This creates a REAL tweet

```bash
python src/main.py --mode post --plan free
```

**Look for**: `[OK] Post created: Tweet ID XXXXX`

## [OK] Verify Tweet (2 min)

```bash
# 1. Check database
python scripts/peek_actions.py --limit 1 --kind post

# 2. Check budget
python src/main.py --safety print-budget

# 3. Visit X.com and verify tweet appears on your profile
```

## [OK] Settle Metrics (After 24-48 Hours)

```bash
# Wait 24-48 hours for engagement, then:
python src/main.py --settle-all
```

**This optimizes future tweets based on performance.**

## [ALERT] Troubleshooting Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "No window active" | Wait for next window or add all windows to config: `[morning, afternoon, evening]` |
| "Authentication failed" | Tweepy: verify `.env` has 4 tokens. OAuth2: rerun `--authorize` |
| "Budget exceeded" | Delete `data/agent_unified.db` and rerun setup (clears old data) |
| Tweet not visible on X | Check spam filter, verify correct account, refresh page |
| "Duplicate content" | Normal! Agent prevents spam. Wait 7 days or change topics in config |

## [TARGET] Success Criteria

- [x] Dry-run passes without errors
- [x] Live run creates tweet (Tweet ID returned)
- [x] Tweet visible on X.com profile
- [x] Database shows 1 action (`peek_actions.py`)
- [x] Budget shows 1 tweet used
- [x] No error messages in console

**All checked?** Success! [PARTY] You're ready to enable more features.

## Next: Enable Full Automation

Once comfortable with single tweets:

1. **Increase limits** in `config.yaml`:
   ```yaml
   max_per_window:
     post: 1
     like: 5
     reply: 2
   ```

2. **Enable both modes**:
   ```bash
   python src/main.py --mode both --plan free
   ```

3. **Schedule runs** (Task Scheduler, cron, or manual)

4. **Monitor & optimize** with `--settle-all` weekly

See [FIRST_TWEET_GUIDE.md](FIRST_TWEET_GUIDE.md) for detailed next steps.
