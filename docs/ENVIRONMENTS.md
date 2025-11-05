# GitHub Environments & Single-Click Deployment 🚀

Complete guide for setting up GitHub environments with maximum automation and minimal human oversight.

## 🎯 Environment Architecture

### Staging Environment
- **Purpose**: Test changes before production
- **Secrets**: Same as production for realistic testing
- **Protection**: None (auto-deploys from PRs)
- **Usage**: Automatic testing, CI/CD validation

# GitHub Environments — staging and production
### Production Environment  
- **Purpose**: Live X agent automation
- **Secrets**: Production X API credentials

## ⚡ Quick Setup (Automated)
```powershell
# Run interactive setup script
.\scripts\gh_env_setup.ps1

# Dry run to see what would happen
.\scripts\gh_env_setup.ps1 -DryRun
```

### Option 2: Bash (Linux/macOS)
```bash
# Run interactive setup script
./scripts/gh_env_setup.sh

# Dry run to see what would happen
./scripts/gh_env_setup.sh --dry-run
```

## 🛠️ Manual Setup (GitHub CLI)

If you prefer manual control or the scripts don't work:

### 1. Create Environments

```bash
# Create production environment 
gh api -X PUT repos/<owner>/<repo>/environments/production -H "Accept: application/vnd.github+json"
```
### 2. Set Secrets for Each Environment

Replace `<owner>` and `<repo>` with your actual values, and set your actual secret values:

```bash
# Set secrets for staging environment
gh secret set -e staging X_CLIENT_ID -b"$Env:X_CLIENT_ID"
gh secret set -e staging X_CLIENT_SECRET -b"$Env:X_CLIENT_SECRET" 
gh secret set -e staging X_REDIRECT_URI -b"$Env:X_REDIRECT_URI"
gh secret set -e staging OPENAI_API_KEY -b"$Env:OPENAI_API_KEY"

# Optional OAuth1 secrets for staging
gh secret set -e staging X_API_KEY -b"$Env:X_API_KEY"
gh secret set -e staging X_API_SECRET -b"$Env:X_API_SECRET"
gh secret set -e staging X_ACCESS_TOKEN -b"$Env:X_ACCESS_TOKEN"
gh secret set -e staging X_ACCESS_SECRET -b"$Env:X_ACCESS_SECRET"

# Set secrets for production environment (same secrets)
gh secret set -e production X_CLIENT_ID -b"$Env:X_CLIENT_ID"
gh secret set -e production X_CLIENT_SECRET -b"$Env:X_CLIENT_SECRET"
gh secret set -e production X_REDIRECT_URI -b"$Env:X_REDIRECT_URI" 
gh secret set -e production OPENAI_API_KEY -b"$Env:OPENAI_API_KEY"

# Optional OAuth1 secrets for production
gh secret set -e production X_API_KEY -b"$Env:X_API_KEY"
gh secret set -e production X_API_SECRET -b"$Env:X_API_SECRET"
gh secret set -e production X_ACCESS_TOKEN -b"$Env:X_ACCESS_TOKEN"
gh secret set -e production X_ACCESS_SECRET -b"$Env:X_ACCESS_SECRET"
```

### 3. Add Production Environment Protection (GitHub UI)

Since production requires manual approval, you need to configure protection rules:

1. **Go to GitHub Repository** → Settings → Environments
2. **Click on "production"** environment
3. **Check "Required reviewers"** 
4. **Add yourself** as the required reviewer
5. **Save protection rules**

This enables **single-click approval** for production deployments via the GitHub UI.

### 4. Alternative: Set Production Protection via API

If you prefer CLI, add protection to production environment:

```bash
# Configure production environment protection (requires your GitHub user ID)
USER_ID=$(gh api user --jq .id)
gh api -X PUT repos/<owner>/<repo>/environments/production -H "Accept: application/vnd.github+json" --input - << EOF
{
  "reviewers": [
    {
      "type": "User", 
      "id": $USER_ID
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
EOF

gh secret set X_ACCESS_TOKEN --env staging
gh secret set X_ACCESS_TOKEN --env production

gh secret set X_ACCESS_SECRET --env staging
gh secret set X_ACCESS_SECRET --env production
```

## 🎮 Single-Click Approval Workflow

### How It Works

1. **GitHub Copilot** creates PR with changes
2. **CI Pipeline** runs automatically:
   - Type checking (`nox -s type`)
   - Unit tests (`nox -s test`) 
   - Dry-run validation (`python src/main.py --dry-run --mode both`)
3. **Auto-merge** happens if tests pass
4. **Production deployment** waits for your approval
5. **You click "Approve"** (single click) 
6. **Live automation** starts with new changes

### GitHub Actions Workflows

**`.github/workflows/ci.yml`** - Continuous Integration
```yaml
# Runs on every PR
# - Tests and type checking
# - Dry-run validation with config.max-automation.yaml
# - Auto-merge if all checks pass
```

**`.github/workflows/deploy-staging.yml`** - Staging Deployment
```yaml
# Runs after PR merge to main
# - Deploys to staging environment automatically
# - No approval required
```

**`.github/workflows/deploy-production.yml`** - Production Deployment  
```yaml
# Manual trigger with single-click approval
# - Uses production environment (requires approval)
# - Runs safety checks before deployment
# - Starts live automation
```

## 🔐 Environment Secrets Reference

### Required for OAuth2 Mode (Recommended)
| Secret | Description | Example |
|--------|-------------|---------|
| `X_CLIENT_ID` | OAuth2 Client ID | `your_client_id_here` |
| `X_CLIENT_SECRET` | OAuth2 Client Secret | `your_client_secret_here` |
| `X_REDIRECT_URI` | OAuth2 Redirect URI | `http://localhost:8080/callback` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |

### Optional for Tweepy Mode (Legacy)
| Secret | Description | Example |
|--------|-------------|---------|
| `X_API_KEY` | Twitter API Key | `your_api_key_here` |
| `X_API_SECRET` | Twitter API Secret | `your_api_secret_here` |
| `X_ACCESS_TOKEN` | Twitter Access Token | `your_access_token_here` |
| `X_ACCESS_SECRET` | Twitter Access Secret | `your_access_secret_here` |

## 📋 Deployment Commands

### Manual Production Deployment
```bash
# Trigger production deployment workflow
gh workflow run deploy-production.yml

# Check deployment status  
gh run list --workflow=deploy-production.yml

# View deployment logs
gh run view --log
```

### Emergency Controls
```bash
# Stop all workflows
gh workflow disable deploy-production.yml
gh workflow disable deploy-staging.yml

# Cancel running deployment
gh run cancel <run-id>

# Re-enable after emergency
gh workflow enable deploy-production.yml
gh workflow enable deploy-staging.yml
```

## 🔍 Monitoring & Validation

### Pre-Deployment Checks
The production deployment includes automatic safety checks:
```bash
# Budget validation
python src/main.py --safety print-budget

# Rate limit check  
python src/main.py --safety print-limits

# Configuration validation
python -c "import src.config_schema; print('✅ Config valid')"
```

### Post-Deployment Monitoring
```bash
# Check live status
gh api repos/:owner/:repo/environments/production/deployments

# View recent actions (if available)
python scripts/peek_actions.py

# Check Thompson Sampling learning
python src/main.py --safety print-learning
```

## 🚨 Troubleshooting

### Common Issues

**"Environment not found" errors:**
- Check repository is public or has GitHub Pro
- Verify you have admin permissions
- Ensure GitHub CLI is authenticated: `gh auth status`

**"Secret not set" errors:**
- Verify secrets exist: `gh secret list --env production`
- Check secret names match exactly (case-sensitive)
- Re-run setup script if secrets are missing

**Approval required but no approval shows:**
- Check environment protection rules
- Ensure you're added as a reviewer
- Try refreshing the Actions page

**Deployment fails with "Invalid credentials":**
- Verify X API credentials are correct and active
- Check OAuth2 scopes include: `tweet.write`, `tweet.read`, `users.read`, `offline.access`
- Test credentials locally first: `python src/main.py --authorize`

### Emergency Procedures

**Stop everything immediately:**
```bash
# Disable all workflows
gh workflow disable-workflow deploy-production.yml
gh workflow disable-workflow deploy-staging.yml
gh workflow disable-workflow auto-merge.yml

# Cancel running jobs
gh run list --status in_progress --json databaseId --jq '.[].databaseId' | xargs -I {} gh run cancel {}
```

**Safe restart:**
```bash
# Test locally first
python src/main.py --dry-run --mode both

# Re-enable workflows gradually  
gh workflow enable deploy-staging.yml
gh workflow enable deploy-production.yml  
gh workflow enable auto-merge.yml
```

## ✅ Success Criteria

After setup, you should have:

- [ ] Staging environment created and accessible
- [ ] Production environment created with approval requirement  
- [ ] All required secrets set in both environments
- [ ] CI workflow runs successfully on PR
- [ ] Staging deployment works automatically
- [ ] Production deployment waits for approval
- [ ] Single-click approval triggers live automation
- [ ] Emergency stop procedures tested and working

## 🎯 Maximum Automation Achieved

With this setup:
- **GitHub Copilot** handles all code changes
- **CI/CD** validates changes automatically
- **Staging** tests everything safely
- **Production** requires just one click from you
- **Emergency controls** let you stop everything instantly

**Result**: Maximum delegation with minimal human oversight, exactly as requested! 🚀

---

**Next**: See `COPILOT_MAX_DELEGATION.md` for complete delegation guide