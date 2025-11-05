# GitHub Environments Setup Script for X Agent
# Creates staging and production environments with secrets

param(
    [switch]$DryRun,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
GitHub Environment Setup for X Agent Maximum Automation

USAGE:
    .\scripts\gh_env_setup.ps1              # Interactive setup
    .\scripts\gh_env_setup.ps1 -DryRun      # Show commands without executing
    .\scripts\gh_env_setup.ps1 -Help        # Show this help

PREREQUISITES:
    - GitHub CLI installed and authenticated: gh auth login
    - Repository must be public or have GitHub Pro for environments
    - You must have admin permissions on the repository

WHAT THIS DOES:
    1. Checks GitHub CLI authentication
    2. Creates 'staging' and 'production' environments using gh api
    3. Sets up environment secrets for X API credentials
    4. Configures environment protection rules (production requires approval)

SECRETS SET:
    Required:
    - X_CLIENT_ID
    - X_CLIENT_SECRET
    - X_REDIRECT_URI
    - OPENAI_API_KEY
    
    Optional (for OAuth1/Tweepy mode):
    - X_API_KEY
    - X_API_SECRET
    - X_ACCESS_TOKEN
    - X_ACCESS_SECRET
"@
    exit 0
}

function Write-Status {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "🔍 $Message" -ForegroundColor Blue
}

function Test-GitHubAuth {
    Write-Info "Checking GitHub CLI authentication..."
    
    try {
        gh auth status --hostname github.com 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "GitHub CLI is authenticated"
            return $true
        } else {
            Write-Error "GitHub CLI not authenticated. Please run: gh auth login"
            return $false
        }
    } catch {
        Write-Error "GitHub CLI not found or not authenticated. Please install and run: gh auth login"
        return $false
    }
}

function New-GitHubEnvironment {
    param($EnvName, $RequireApproval = $false)
    
    Write-Host "`n🔧 Configuring environment: $EnvName"
    
    if ($DryRun) {
        Write-Host "[DRY RUN] gh api repos/:owner/:repo/environments/$EnvName -X PUT"
        if ($RequireApproval) {
            Write-Host "[DRY RUN] Would set protection rules requiring approval for $EnvName"
        }
        return $true
    }
    
    # Create environment using gh api
    try {
        Write-Info "Creating environment: $EnvName"
        gh api "repos/:owner/:repo/environments/$EnvName" -X PUT | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Environment '$EnvName' created"
        } else {
            Write-Warning "Environment '$EnvName' may already exist"
        }
    } catch {
        Write-Warning "Environment '$EnvName' creation issue: $($_.Exception.Message)"
    }
    
    # Set protection rules for production
    if ($RequireApproval -and $EnvName -eq "production") {
        try {
            Write-Info "Setting protection rules for production environment"
            
            # Get current user ID
            $userId = gh api user --jq .id
            
            # Create protection rules using temporary file (PowerShell-compatible approach)
            $tempFile = [System.IO.Path]::GetTempFileName()
            $protectionJson = @"
{
  "reviewers": [
    {
      "type": "User", 
      "id": $userId
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  },
  "wait_timer": 0
}
"@
            $protectionJson | Set-Content $tempFile
            
            # Apply protection rules
            gh api "repos/:owner/:repo/environments/$EnvName" -X PUT --input $tempFile | Out-Null
            Remove-Item $tempFile -ErrorAction SilentlyContinue
            
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Production environment configured with single-reviewer approval"
            } else {
                Write-Warning "Could not set protection rules for production"
            }
        } catch {
            Write-Warning "Could not set protection rules for production: $($_.Exception.Message)"
        }
    }
    
    return $true
}

function Set-EnvironmentSecret {
    param($EnvName, $SecretName, $SecretValue)
    
    if ([string]::IsNullOrWhiteSpace($SecretValue)) {
        Write-Host "  Skipping empty secret: $SecretName" -ForegroundColor Gray
        return
    }
    
    if ($DryRun) {
        Write-Host "[DRY RUN] gh secret set $SecretName --env $EnvName --body `"<VALUE>`""
        return
    }
    
    try {
        Write-Host "  Setting secret: $SecretName" -ForegroundColor Cyan
        $SecretValue | gh secret set $SecretName --env $EnvName
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Secret '$SecretName' set in $EnvName"
        } else {
            Write-Error "Failed to set secret '$SecretName' in $EnvName"
        }
    } catch {
        Write-Error "Failed to set secret '$SecretName' in $EnvName`: $($_.Exception.Message)"
    }
}

# Main script execution
Write-Host @"
🚀 GitHub Environment Setup for X Agent Maximum Automation
========================================================

This script will create GitHub environments and set secrets for:
- staging: For testing changes with real credentials
- production: For live automation (requires single approval click)

"@

# Check prerequisites
if (!(Test-GitHubAuth)) {
    exit 1
}

# Verify we're in the correct repository
if (!(Test-Path "src/main.py")) {
    Write-Error "Not in X Agent repository root. Please run from repository root directory."
    exit 1
}

if ($DryRun) {
    Write-Host "`n🔍 DRY RUN MODE - No changes will be made, only commands will be shown`n" -ForegroundColor Cyan
}

# Collect secrets interactively
Write-Host "`n🔐 Collecting secrets for both environments..."
Write-Host "Enter values for the following secrets (press Enter to skip optional ones):`n"

$secrets = @{}

# Required OAuth2 secrets
Write-Host "Required OAuth2/X API credentials:" -ForegroundColor Yellow
$secrets['X_CLIENT_ID'] = Read-Host "X_CLIENT_ID (OAuth2 Client ID)"
$secrets['X_CLIENT_SECRET'] = Read-Host "X_CLIENT_SECRET (OAuth2 Client Secret)" -MaskInput
$secrets['X_REDIRECT_URI'] = Read-Host "X_REDIRECT_URI (OAuth2 Redirect URI, e.g., http://localhost:8080/callback)"
$secrets['OPENAI_API_KEY'] = Read-Host "OPENAI_API_KEY (OpenAI API Key)" -MaskInput

# Optional OAuth1/Tweepy secrets
Write-Host "`nOptional OAuth1/Tweepy credentials (for legacy mode):" -ForegroundColor Yellow
$secrets['X_API_KEY'] = Read-Host "X_API_KEY (Optional: Twitter API Key for Tweepy mode)"
$secrets['X_API_SECRET'] = Read-Host "X_API_SECRET (Optional: Twitter API Secret for Tweepy mode)" -MaskInput
$secrets['X_ACCESS_TOKEN'] = Read-Host "X_ACCESS_TOKEN (Optional: Twitter Access Token for Tweepy mode)" -MaskInput
$secrets['X_ACCESS_SECRET'] = Read-Host "X_ACCESS_SECRET (Optional: Twitter Access Secret for Tweepy mode)" -MaskInput

# Create environments
Write-Host "`n🏗️  Creating environments..."

if (!(New-GitHubEnvironment "staging" $false)) {
    Write-Error "Failed to create staging environment"
    exit 1
}

if (!(New-GitHubEnvironment "production" $true)) {
    Write-Error "Failed to create production environment"  
    exit 1
}

# Set secrets for both environments
$environments = @("staging", "production")

foreach ($env in $environments) {
    Write-Host "`n🔑 Setting secrets for environment: $env"
    
    foreach ($secretName in $secrets.Keys) {
        Set-EnvironmentSecret $env $secretName $secrets[$secretName]
    }
}

# Summary
Write-Host "`n🎯 Setup Summary:" -ForegroundColor Green
Write-Host "=================="
Write-Status "Staging environment: Ready for automatic deployments"
Write-Status "Production environment: Requires single approval click"
Write-Host ""

if (!$DryRun) {
    Write-Host @"
✅ Environment setup complete!

Next steps:
1. Go to GitHub → Settings → Environments  
2. Verify 'production' has 'Required reviewers' set to your user
3. Test deployment with: gh workflow run live-post.yml

Ready for maximum GitHub Copilot delegation!
"@
} else {
    Write-Host @"
🔍 DRY RUN COMPLETE - No changes made

To actually create environments, run:
  .\scripts\gh_env_setup.ps1

Or set secrets manually with:
  gh secret set X_CLIENT_ID --env staging --body "your_client_id"
  gh secret set X_CLIENT_ID --env production --body "your_client_id"
  # (repeat for all secrets)
"@
}

Write-Host ""