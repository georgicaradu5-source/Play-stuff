# Migration Guide: Moving to X Agent Unified

This guide helps you migrate from either `agent-x` or `x-agent` to the new unified implementation.

## Why Migrate?

**x-agent-unified** combines the best of both:
- ✅ Dual auth support (Tweepy OR OAuth 2.0)
- ✅ Thompson Sampling learning
- ✅ Enterprise budget management
- ✅ Advanced rate limiting
- ✅ Time-window scheduling
- ✅ All features in one place

## Migration Paths

### Option A: From agent-x (Tweepy + Learning)

**What You Keep:**
- ✅ Tweepy authentication (same credentials)
- ✅ Thompson Sampling learning
- ✅ Time-window scheduling
- ✅ Template-based content
- ✅ Existing database (compatible schema)

**What You Gain:**
- ✅ Option to use OAuth 2.0 PKCE
- ✅ Plan-tier budget management
- ✅ Advanced rate limiting
- ✅ Better error handling

**Steps:**

1. **Copy your credentials**:
   ```bash
   # Copy existing .env
   cp agent-x/.env x-agent-unified/.env

   # Add auth mode
   echo "X_AUTH_MODE=tweepy" >> x-agent-unified/.env
   ```

2. **Copy your config** (optional):
   ```bash
   cp agent-x/config.yaml x-agent-unified/config.yaml
   ```

3. **Install dependencies**:
   ```bash
   cd x-agent-unified
   pip install -r requirements.txt
   ```

4. **Test**:
   ```bash
   python src/main.py --mode both --dry-run true
   ```

5. **Run**:
   ```bash
   python src/main.py --mode both
   ```

**Database Note**: The unified agent uses a new database (`data/agent_unified.db`) with a compatible schema. Your old data remains untouched.

---

### Option B: From x-agent (OAuth 2.0 + Safety)

**What You Keep:**
- ✅ OAuth 2.0 PKCE authentication
- ✅ Token file (`.token.json`)
- ✅ Plan-tier budget management
- ✅ Rate limiting
- ✅ Action history

**What You Gain:**
- ✅ Option to use Tweepy (simpler)
- ✅ Thompson Sampling learning
- ✅ Time-window scheduling
- ✅ Template-based content
- ✅ Bandit optimization

**Steps:**

1. **Copy your credentials**:
   ```bash
   # Copy existing .env
   cp x-agent/.env x-agent-unified/.env

   # Ensure auth mode is set
   echo "X_AUTH_MODE=oauth2" >> x-agent-unified/.env
   ```

2. **Copy your token file**:
   ```bash
   cp x-agent/.token.json x-agent-unified/.token.json
   ```

3. **Copy your config** (optional):
   ```bash
   cp x-agent/config.yaml x-agent-unified/config.yaml
   ```

4. **Install dependencies**:
   ```bash
   cd x-agent-unified
   pip install -r requirements.txt
   ```

5. **Test**:
   ```bash
   python src/main.py --mode both --dry-run true
   ```

6. **Run**:
   ```bash
   python src/main.py --mode both
   ```

**Database Note**: The unified agent uses a new database with an expanded schema including learning tables.

---

## Configuration Mapping

### agent-x → unified

| agent-x | x-agent-unified | Notes |
|---------|-----------------|-------|
| `topics` | `topics` | Same |
| `queries` | `queries` | Same |
| `schedule.windows` | `schedule.windows` | Same |
| `cadence.weekdays` | `cadence.weekdays` | Same |
| `max_per_window` | `max_per_window` | Same |
| `jitter_seconds` | `jitter_seconds` | Same |
| N/A | `learning.enabled` | New: control Thompson Sampling |
| N/A | `budget.buffer_pct` | New: safety buffer |
| N/A | `plan` | New: free/basic/pro |

### x-agent → unified

| x-agent | x-agent-unified | Notes |
|---------|-----------------|-------|
| `plan` | `plan` | Same |
| `budget.buffer_pct` | `budget.buffer_pct` | Same |
| `queries` | `queries` | Same |
| N/A | `topics` | New: for learning |
| N/A | `learning.enabled` | New: Thompson Sampling |
| N/A | `schedule.windows` | New: time windows |
| N/A | `cadence.weekdays` | New: day filtering |

---

## Feature Comparison

| Feature | agent-x | x-agent | unified |
|---------|---------|---------|---------|
| **Auth: Tweepy** | ✅ | ❌ | ✅ |
| **Auth: OAuth 2.0** | ❌ | ✅ | ✅ |
| **Learning Loop** | ✅ | ❌ | ✅ |
| **Time Windows** | ✅ | ❌ | ✅ |
| **Plan Tiers** | ❌ | ✅ | ✅ |
| **Rate Limiting** | Basic | Advanced | Advanced |
| **Templates** | ✅ | ❌ | ✅ |
| **Budget Manager** | Basic | Advanced | Advanced |

---

## CLI Command Mapping

### agent-x → unified

```bash
# agent-x
python src/main.py --mode both --dry-run true
python src/main.py --settle-all

# unified (same!)
python src/main.py --mode both --dry-run true
python src/main.py --settle-all
```

### x-agent → unified

```bash
# x-agent
python src/main.py --authorize
python src/main.py --dry-run --mode both

# unified (almost the same)
python src/main.py --authorize
python src/main.py --mode both --dry-run true
```

---

## Database Migration

### Schema Changes

The unified agent adds these tables:
- `bandit` - Thompson Sampling learning data
- `usage_daily` - Daily usage tracking
- `api_calls` - Detailed API call logging

**Existing data preserved**: Your old databases remain untouched. The unified agent creates a new database.

### Migrating Learning Data (Advanced)

If you want to migrate learning data from `agent-x`:

```sql
-- Copy bandit data from agent-x to unified
sqlite3 agent-x/data/agent.db "SELECT * FROM bandit" |
sqlite3 x-agent-unified/data/agent_unified.db ".import /dev/stdin bandit"
```

---

## Troubleshooting

### "Missing X API credentials"

**Solution**: Copy your `.env` file from old agent or create new one.

```bash
cp agent-x/.env x-agent-unified/.env
# OR
cp x-agent/.env x-agent-unified/.env
```

### "Module not found"

**Solution**: Install dependencies in unified directory.

```bash
cd x-agent-unified
pip install -r requirements.txt
```

### "Authorization failed" (OAuth 2.0)

**Solution**: Run authorization flow again.

```bash
python src/main.py --authorize
```

### "Database locked"

**Solution**: Close old agent before running unified.

---

## Rollback Plan

If you need to revert:

1. **Old agents still work** - They're untouched
2. **Separate databases** - No data loss
3. **Switch back anytime**:
   ```bash
   cd agent-x  # or x-agent
   python src/main.py --mode both
   ```

---

## Gradual Migration

**Recommended approach**:

1. **Week 1**: Test unified in dry-run mode
   ```bash
   python src/main.py --mode both --dry-run true
   ```

2. **Week 2**: Run both agents side-by-side
   - Keep old agent running
   - Add unified agent with lower limits

3. **Week 3**: Settle metrics and compare
   ```bash
   python src/main.py --settle-all
   python src/main.py --safety print-learning
   ```

4. **Week 4**: Full cutover to unified

---

## Support

- **Issues**: File on GitHub
- **Questions**: Check README.md and QUICKSTART.md
- **Old agents**: Preserved in `agent-x/` and `x-agent/` directories

---

## Benefits After Migration

✅ **Flexibility**: Switch auth modes anytime
✅ **Learning**: Auto-optimize your strategy
✅ **Safety**: Enterprise-grade budgets + rate limits
✅ **Features**: All capabilities in one place
✅ **Future-proof**: Active development continues here

**Ready to migrate?** Follow the steps above and you'll be running in minutes!
