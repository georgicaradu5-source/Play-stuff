# Archive - Legacy X Agent Implementations

This directory contains the two previous X agent implementations that were unified into the current solution.

## Why These Are Archived

Both implementations were functional and production-ready, but maintaining three separate codebases was inefficient. The current unified agent (at the repository root) combines the best features from both.

## Archived Projects

### agent-x/ - Tweepy + Learning Implementation

**Original Author**: ChatGPT Codex  
**Auth Method**: OAuth 1.0a (Tweepy)  
**Key Features**:
- Thompson Sampling learning loop
- Time-window scheduling (morning/afternoon/evening)
- Template-based content generation
- Jaccard similarity deduplication

**Status**: Fully functional, superseded by unified agent

---

### x-agent/ - OAuth 2.0 + Safety Implementation

**Original Author**: GitHub Copilot  
**Auth Method**: OAuth 2.0 PKCE  
**Key Features**:
- Modern OAuth 2.0 PKCE authentication
- Plan-tier budget management (Free/Basic/Pro)
- Advanced rate limiting with backoff
- Comprehensive error handling

**Status**: Fully functional, superseded by unified agent

---

## What's in the Unified Agent?

The unified agent (at repository root) includes:

✅ **Both auth methods** (Tweepy + OAuth 2.0)  
✅ **Thompson Sampling** from agent-x  
✅ **Time windows** from agent-x  
✅ **Plan tiers** from x-agent  
✅ **Rate limiting** from x-agent  
✅ **All features** from both  

## Migration

If you were using one of these legacy agents, see the migration guide in the root directory:

```bash
# Read the migration guide
cat ../MIGRATION.md

# Copy your credentials
cp agent-x/.env ../.env
# OR
cp x-agent/.env ../.env

# Run the unified agent
cd ..
python src/main.py --mode both --dry-run true
```

## Still Want to Use Legacy Agents?

They still work! Both are fully functional:

```bash
# Use agent-x
cd _archive/agent-x
python src/main.py --mode both

# Use x-agent
cd _archive/x-agent
python src/main.py --mode both
```

However, future development and improvements will only happen in the unified agent.

## Historical Reference

These implementations are preserved for:
- Reference and learning
- Understanding design evolution
- Comparing architectural approaches
- Migration support

**Recommendation**: Use the unified agent at the repository root for new projects.
