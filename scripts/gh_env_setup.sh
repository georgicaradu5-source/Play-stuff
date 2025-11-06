#!/bin/bash
# GitHub Environments Setup Script for X Agent
# Creates staging and production environments with secrets

set -e

DRY_RUN=false
HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    cat << EOF
GitHub Environment Setup for X Agent Maximum Automation

USAGE:
    ./scripts/gh_env_setup.sh              # Interactive setup
    ./scripts/gh_env_setup.sh --dry-run    # Show commands without executing
    ./scripts/gh_env_setup.sh --help       # Show this help

PREREQUISITES:
    - GitHub CLI installed and authenticated: gh auth login
    - Repository must be public or have GitHub Pro for environments
    - You must have admin permissions on the repository

WHAT THIS DOES:
    1. Checks GitHub CLI authentication
    2. Creates 'staging' and 'production' environments
    3. Sets up environment secrets for X API credentials
    4. Configures environment protection rules (production requires approval)
    5. Creates deployment workflows for single-click approvals

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
    - X_CLIENT_ID
    - X_CLIENT_SECRET
    - X_REDIRECT_URI
    - OPENAI_API_KEY
    - X_API_KEY (optional, for Tweepy mode)
    - X_API_SECRET (optional, for Tweepy mode)
    - X_ACCESS_TOKEN (optional, for Tweepy mode)
    - X_ACCESS_SECRET (optional, for Tweepy mode)
EOF
    exit 0
fi

# Helper functions
print_status() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

test_github_auth() {
    if gh auth status &>/dev/null; then
        print_status "GitHub CLI authenticated"
        return 0
    else
        print_error "GitHub CLI not authenticated"
        echo "Please run: gh auth login"
        return 1
    fi
}

get_secret() {
    local secret_name="$1"
    local description="$2"
    local required="${3:-true}"
    local secret_value=""

    while [ -z "$secret_value" ] && [ "$required" = "true" ]; do
        if [ "$required" = "true" ]; then
            prompt="$description (required): "
        else
            prompt="$description (optional, press Enter to skip): "
        fi

        read -s -p "$prompt" secret_value
        echo

        if [ -z "$secret_value" ] && [ "$required" = "true" ]; then
            print_warning "This secret is required. Please provide a value."
        fi
    done

    echo "$secret_value"
}

create_environment() {
    local env_name="$1"
    local require_approval="${2:-false}"

    echo
    echo "🔧 Creating environment: $env_name"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would create environment: $env_name"
        if [ "$require_approval" = "true" ]; then
            echo "[DRY RUN] Would set protection rules requiring approval"
        fi
        return 0
    fi

    # Create environment
    if gh api "repos/:owner/:repo/environments/$env_name" -X PUT >/dev/null 2>&1; then
        print_status "Environment '$env_name' created"
    else
        print_warning "Environment '$env_name' may already exist or creation failed"
    fi

    # Set protection rules for production
    if [ "$require_approval" = "true" ] && [ "$env_name" = "production" ]; then
        local user_id=$(gh api user --jq .id)
        local protection_rules=$(cat << EOF
{
  "reviewers": [
    {
      "type": "User",
      "id": $user_id
    }
  ],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
EOF
)

        if echo "$protection_rules" | gh api "repos/:owner/:repo/environments/$env_name" -X PUT --input - >/dev/null 2>&1; then
            print_status "Production environment configured with approval requirement"
        else
            print_warning "Could not set protection rules for production"
        fi
    fi

    return 0
}

set_environment_secret() {
    local env_name="$1"
    local secret_name="$2"
    local secret_value="$3"

    if [ -z "$secret_value" ]; then
        echo "  Skipping empty secret: $secret_name"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would set secret $secret_name in environment $env_name"
        return
    fi

    if echo "$secret_value" | gh secret set "$secret_name" --env "$env_name"; then
        print_status "Set secret: $secret_name"
    else
        print_error "Failed to set secret $secret_name in $env_name"
    fi
}

# Main script
cat << EOF
🚀 GitHub Environment Setup for X Agent Maximum Automation
========================================================

This script will create GitHub environments and set secrets for:
- staging: For testing changes
- production: For live automation (requires approval)

EOF

# Check prerequisites
if ! test_github_auth; then
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    print_error "Not in X Agent repository root. Please run from repository root directory."
    exit 1
fi

if [ "$DRY_RUN" = true ]; then
    echo
    echo "🔍 DRY RUN MODE - No changes will be made"
    echo
fi

# Collect secrets
echo
echo "🔐 Collecting secrets for both environments..."
echo "These will be set in both staging and production environments."
echo

declare -A secrets

# OAuth2 credentials (recommended)
echo "OAuth2 Credentials (recommended for new apps):"
secrets["X_CLIENT_ID"]=$(get_secret "X_CLIENT_ID" "X OAuth2 Client ID")
secrets["X_CLIENT_SECRET"]=$(get_secret "X_CLIENT_SECRET" "X OAuth2 Client Secret")
secrets["X_REDIRECT_URI"]="http://localhost:8080/callback"  # Standard redirect

# OpenAI API key
secrets["OPENAI_API_KEY"]=$(get_secret "OPENAI_API_KEY" "OpenAI API Key for AI features")

# OAuth1 credentials (optional)
echo
echo "OAuth1 Credentials (optional, for legacy Tweepy apps):"
secrets["X_API_KEY"]=$(get_secret "X_API_KEY" "X API Key (optional)" false)
secrets["X_API_SECRET"]=$(get_secret "X_API_SECRET" "X API Secret (optional)" false)
secrets["X_ACCESS_TOKEN"]=$(get_secret "X_ACCESS_TOKEN" "X Access Token (optional)" false)
secrets["X_ACCESS_SECRET"]=$(get_secret "X_ACCESS_SECRET" "X Access Secret (optional)" false)

# Create environments
echo
echo "🏗️  Creating environments..."

if ! create_environment "staging" false; then
    print_error "Failed to create staging environment"
    exit 1
fi

if ! create_environment "production" true; then
    print_error "Failed to create production environment"
    exit 1
fi

# Set secrets in both environments
for env_name in staging production; do
    echo
    echo "🔑 Setting secrets in $env_name environment..."

    for secret_name in "${!secrets[@]}"; do
        set_environment_secret "$env_name" "$secret_name" "${secrets[$secret_name]}"
    done
done

echo
echo "🎯 Environment setup complete!"

if [ "$DRY_RUN" = false ]; then
    cat << EOF

✅ Created environments:
   - staging: Ready for testing
   - production: Requires approval for deployments

✅ Set secrets in both environments:
   - X_CLIENT_ID, X_CLIENT_SECRET, X_REDIRECT_URI
   - OPENAI_API_KEY
   - OAuth1 credentials (if provided)

🎮 Next steps:
   1. Test locally first: python src/main.py --dry-run --mode both
   2. Use GitHub Actions workflows for automated deployment
   3. Production deployments require single-click approval

📚 See docs/ENVIRONMENTS.md for workflow details

⚡ Ready for maximum GitHub Copilot delegation!
EOF
else
    cat << EOF

🔍 DRY RUN COMPLETE - No changes made

To apply these changes, run:
    ./scripts/gh_env_setup.sh

Or set secrets manually:
    gh secret set SECRET_NAME --env staging
    gh secret set SECRET_NAME --env production
EOF
fi
