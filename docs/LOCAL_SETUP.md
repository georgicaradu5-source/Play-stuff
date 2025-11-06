# X Agent - Local Setup Checklist [ROCKET]

Quick 1-page guide to get your X agent running locally with maximum automation.

## [OK] Prerequisites

- [ ] **Python 3.11+** installed
- [ ] **Git** installed and repository cloned
- [ ] **X Developer Account** with app created at [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard)
- [ ] **GitHub CLI** installed and authenticated: `gh auth login`

## [OK] Step 1: Environment Configuration

### Copy and edit environment file:
```powershell
# Copy template
Copy-Item .env.example .env

# Edit with your credentials
notepad .env
```

### Required credentials to add to `.env`:

**For OAuth2 mode (recommended):**
```bash
X_CLIENT_ID=your_actual_client_id_here
X_CLIENT_SECRET=your_actual_client_secret_here
OPENAI_API_KEY=your_openai_key_here  # For AI features
```

**For Tweepy mode (legacy):**
```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_secret_here
OPENAI_API_KEY=your_openai_key_here
```

## [OK] Step 2: Choose Configuration Level

### Option A: Safe Start (Recommended)
```powershell
# Use conservative config for testing
Copy-Item config.safe.yaml config.yaml
```

### Option B: Maximum Automation
```powershell
# Use max automation config (already active)
# config.yaml is already set to maximum automation
```

## [OK] Step 3: Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import tweepy, requests, yaml; print('[OK] Dependencies OK')"
```

## [OK] Step 4: Authorize OAuth2 (First Time Only)

```powershell
# Start OAuth2 authorization flow
python src/main.py --authorize

# Follow browser prompts to authorize
# Token will be saved to .token.json automatically
```

## [OK] Step 5: Test with Dry Run

```powershell
# Test both modes without posting
python src/main.py --dry-run --mode both

# Check for any errors in output
# Should show "DRY RUN" in all operations
```

## [OK] Step 6: Safety Check

```powershell
# Check budget limits
python src/main.py --safety print-budget

# Check rate limits  
python src/main.py --safety print-limits

# Both should show reasonable values
```

## [OK] Step 7: Go Live (When Ready)

### Single post test:
```powershell
# Post once and exit
python src/main.py --mode post
```

### Full automation:
```powershell
# Start full automation (posts + interactions)
python src/main.py --mode both
```

### Interact only:
```powershell
# Interactions without posting
python src/main.py --mode interact  
```

## [TOOLS] Troubleshooting

### Common Issues:

**"No module named X" errors:**
```powershell
pip install -r requirements.txt --upgrade
```

**OAuth2 authorization fails:**
- Verify X_CLIENT_ID and X_CLIENT_SECRET in `.env`
- Check redirect URI matches: `http://localhost:8080/callback`
- Ensure app has OAuth2 enabled in X Developer portal

**Rate limit errors:**
- Use `--safety print-limits` to check current usage
- Wait for reset time or use dry-run mode

**Empty queries/no content:**
- Check config.yaml has topics and queries defined
- Verify internet connection for search queries

## [GAME] Advanced: GitHub Environment Setup

After local testing works, set up staging/production environments:

```powershell
# Run environment setup script
.\scripts\gh_env_setup.ps1

# Follow prompts to create GitHub environments
# Add same credentials as secrets in GitHub
```

## [CHART] Monitoring

```powershell
# View recent actions
python scripts/peek_actions.py  # If available

# Thompson Sampling stats
python src/main.py --safety print-learning
```

## [WARN] Safety Notes

- Start with `config.safe.yaml` for initial testing
- Always test with `--dry-run` first
- Monitor rate limits with `--safety` commands
- Keep `.env` and `.token.json` private (never commit)

## [TARGET] Success Criteria

- [ ] OAuth2 authorization completes successfully
- [ ] Dry-run shows realistic actions without errors
- [ ] Safety checks show expected budget/limit values  
- [ ] Single post test works without rate limit errors
- [ ] Full automation runs for 5+ minutes without crashes

**Time estimate:** 15-30 minutes for complete setup

---

**Next:** See `docs/ENVIRONMENTS.md` for GitHub staging/production setup