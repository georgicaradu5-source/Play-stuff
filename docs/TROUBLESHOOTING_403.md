# 403 Forbidden Error - X API Permissions Required

## Issue
Attempted live post verification resulted in `403 Forbidden` error when calling `POST /2/tweets`.

## Diagnosis
✅ OAuth2 token has correct scopes: `tweet.write`, `tweet.read`, `like.write`, `follows.write`, `offline.access`
❌ X Developer App permissions likely set to **"Read Only"** in the portal

## Resolution Steps

### 1. Check App Permissions in X Developer Portal
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Navigate to **Settings > User authentication settings**
4. Verify **App permissions** is set to **"Read and write"** (or "Read and write and Direct message")

### 2. If Permissions Are "Read Only"
1. Click **Edit** next to App permissions
2. Select **"Read and write"**
3. Save changes
4. **Re-authorize the app** (old tokens won't inherit new permissions)

### 3. Re-authorize Agent
```pwsh
# Delete old token
Remove-Item .token.json

# Run authorization again
python src/main.py --authorize
```

### 4. Retry Verification
```pwsh
# Enable all days temporarily for verification
# (Edit config.yaml: weekdays: [1, 2, 3, 4, 5, 6, 7])

# Run single live post
python src/main.py --mode post --dry-run false

# After successful post, revert config.yaml weekdays to [1, 2, 3, 4, 5]
```

## Alternative: Use Tweepy Mode (OAuth 1.0a)
If you have OAuth 1.0a credentials with write access:

```pwsh
# Update .env
$env:X_AUTH_MODE = 'tweepy'

# Configure OAuth 1.0a credentials in .env:
# X_API_KEY=...
# X_API_SECRET=...
# X_ACCESS_TOKEN=...
# X_ACCESS_SECRET=...

# Run verification
python src/main.py --mode post --dry-run false
```

## Status
- ✅ Authorization flow working (tokens obtained)
- ✅ Dry-run mode verified
- ✅ Config validated and set to safe limits
- ⏸️  Live posting blocked by app permissions (user action required)

**Next:** Update X app permissions to "Read and write", re-authorize, then retry.
