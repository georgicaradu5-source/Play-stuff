# Maximum Automation Setup Script
# Run this to configure your repository for maximum GitHub Copilot delegation

Write-Host "🚀 Configuring repository for MAXIMUM AUTOMATION..." -ForegroundColor Green

# 1. Copy the maximum automation config as default
if (Test-Path "config.max-automation.yaml") {
    Copy-Item "config.max-automation.yaml" "config.yaml"
    Write-Host "✅ Maximum automation config activated" -ForegroundColor Green
} else {
    Write-Host "❌ config.max-automation.yaml not found" -ForegroundColor Red
}

# 2. Set up environment variables for automation
$envContent = @"
# X Agent - Maximum Automation Configuration
X_AUTH_MODE=oauth2
X_CLIENT_ID=your_oauth2_client_id
X_CLIENT_SECRET=your_oauth2_client_secret

# Optional: Tweepy fallback (for v1.1 media uploads)
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret

# Automation Settings
AUTOMATION_LEVEL=maximum
HUMAN_APPROVAL_REQUIRED=false
AUTO_MERGE_ENABLED=true
AUTO_DEPLOY_ENABLED=true
TELEMETRY_ENABLED=true

# Agent Persona
BITCOIN_ADDRESS=your_bitcoin_address_for_tips
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ .env template created (add your credentials)" -ForegroundColor Green

# 3. Install Python dependencies
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️ Python not found - install manually" -ForegroundColor Yellow
}

# 4. Set up Git hooks for automation
$preCommitHook = @"
#!/bin/sh
# Auto-format before commit
python -m black src/ tests/ --quiet || true
python -m ruff --fix src/ tests/ --quiet || true
"@

New-Item -ItemType Directory -Path ".git/hooks" -Force | Out-Null
$preCommitHook | Out-File -FilePath ".git/hooks/pre-commit" -Encoding ASCII
Write-Host "✅ Git hooks configured" -ForegroundColor Green

# 5. Configure GitHub CLI if available
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "⚙️ Configuring GitHub repository settings..." -ForegroundColor Cyan

    # Enable auto-merge
    gh api repos/georgicaradu5-source/Play-stuff --method PATCH --field allow_auto_merge=true | Out-Null
    gh api repos/georgicaradu5-source/Play-stuff --method PATCH --field delete_branch_on_merge=true | Out-Null

    # Enable all repository features
    gh repo edit --enable-issues --enable-wiki --enable-projects | Out-Null

    Write-Host "✅ GitHub repository configured for automation" -ForegroundColor Green
} else {
    Write-Host "⚠️ GitHub CLI not found - configure manually" -ForegroundColor Yellow
}

# 6. Create initial curated content directories
New-Item -ItemType Directory -Path "curated" -Force | Out-Null

$curatedTweets = @"
# Maximum automation curated tweet IDs
# Add tweet IDs here for guaranteed engagement

# Example high-engagement tech tweets
1234567890123456789
"@

$curatedAccounts = @"
# Maximum automation curated accounts
# Add influential accounts to monitor

# Tech leaders and influencers
microsoft
satyanadella
github
openai
elonmusk
sundarpichai
"@

$curatedTweets | Out-File -FilePath "curated/tweet_ids.txt" -Encoding UTF8
$curatedAccounts | Out-File -FilePath "curated/accounts.txt" -Encoding UTF8
Write-Host "✅ Curated content templates created" -ForegroundColor Green

# 7. Display next steps
Write-Host "`n🎯 MAXIMUM AUTOMATION SETUP COMPLETE!" -ForegroundColor Green -BackgroundColor Black
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Add your X API credentials to .env" -ForegroundColor White
Write-Host "2. Run: python src/main.py --authorize (for OAuth2)" -ForegroundColor White
Write-Host "3. Test: python src/main.py --dry-run --mode both" -ForegroundColor White
Write-Host "4. Go live: python src/main.py --mode both" -ForegroundColor White
Write-Host "`nAutomation features enabled:" -ForegroundColor Cyan
Write-Host "• Maximum per-window limits (500 likes, 100 follows, 50 replies)" -ForegroundColor Green
Write-Host "• 24/7 posting schedule (6 time windows)" -ForegroundColor Green
Write-Host "• Hybrid mode (search + curated)" -ForegroundColor Green
Write-Host "• All feature flags enabled" -ForegroundColor Green
Write-Host "• Aggressive Thompson Sampling" -ForegroundColor Green
Write-Host "• Minimal safety buffers" -ForegroundColor Green
Write-Host "• Auto-merge workflows" -ForegroundColor Green
Write-Host "• Copilot full permissions" -ForegroundColor Green

Write-Host "`n⚡ READY FOR MAXIMUM DELEGATION TO GITHUB COPILOT!" -ForegroundColor Green -BackgroundColor DarkBlue
