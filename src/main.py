"""Unified X Agent CLI - combining best features from both agents."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from logger import configure_logging, get_logger

logger = get_logger(__name__)


def load_config(path: str, validate: bool = True) -> dict[str, Any]:
    """Load configuration from YAML file with optional validation.
    
    Args:
        path: Path to configuration file
        validate: If True, validate using Pydantic schema
    
    Returns:
        Configuration dictionary
    """
    if not Path(path).exists():
        logger.warning(f"Config file not found: {path}")
        logger.info("Using default configuration")
        return get_default_config()
    
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")
    
    # Try to validate with Pydantic if available and requested
    if validate:
        try:
            from config_schema import validate_config
            
            is_valid, error_msg, config_obj = validate_config(path)
            if is_valid and config_obj:
                logger.debug(f"Config validated successfully from {path}")
                return config_obj.to_dict()
            elif error_msg:
                logger.warning(f"Config validation failed: {error_msg}")
                logger.info("Loading config without validation (backward compatibility)")
                # Fall through to basic loading
        except ImportError:
            logger.debug("Pydantic not available, skipping validation")
        except Exception as e:
            logger.warning(f"Validation error: {e}, falling back to basic loading")
    
    # Basic loading (backward compatibility)
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
        logger.debug(f"Loaded config from {path}")
        return config


def get_default_config() -> dict[str, Any]:
    """Get default configuration."""
    return {
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["power-platform", "data-viz", "automation"],
        "queries": [
            '(Power BI OR "Power Platform") lang:en -is:retweet -is:reply',
            '("data visualization" OR DAX) lang:en -is:retweet -is:reply',
        ],
        "schedule": {
            "windows": ["morning", "afternoon", "evening"],
        },
        "cadence": {
            "weekdays": [1, 2, 3, 4, 5],
        },
        "max_per_window": {
            "post": 1,
            "reply": 3,
            "like": 10,
            "follow": 3,
            "repost": 1,
        },
        "jitter_seconds": [8, 20],
        "learning": {
            "enabled": True,
        },
        "budget": {
            "buffer_pct": 0.05,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="X Agent Unified - Production-ready X (Twitter) agent with dual auth support"
    )
    
    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["post", "interact", "both"],
        default="both",
        help="Operating mode: post, interact, or both",
    )
    
    # Dry run
    parser.add_argument(
        "--dry-run",
        type=lambda x: x.lower() in ("true", "yes", "1"),
        default=False,
        help="Run without making actual API calls (default: false)",
    )
    
    # OAuth 2.0 authorization
    parser.add_argument(
        "--authorize",
        action="store_true",
        help="Perform OAuth 2.0 PKCE authorization flow (OAuth2 mode only)",
    )
    
    # Learning operations
    parser.add_argument(
        "--settle",
        type=str,
        metavar="POST_ID",
        help="Fetch metrics for a specific post and update learning (requires POST_ID)",
    )
    
    parser.add_argument(
        "--settle-all",
        action="store_true",
        help="Fetch metrics for all owned posts and update learning",
    )
    
    # Safety/diagnostics
    parser.add_argument(
        "--safety",
        choices=["print-budget", "print-limits", "print-learning"],
        help="Print safety/diagnostic information",
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    
    parser.add_argument(
        "--plan",
        choices=["free", "basic", "pro"],
        help="Override plan tier from config",
    )
    
    args = parser.parse_args()
    
    # Load configuration (with validation)
    try:
        config = load_config(args.config, validate=True)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Configure logging from config
    configure_logging(config)
    logger = get_logger(__name__)
    
    # Override plan if specified
    if args.plan:
        config["plan"] = args.plan
        logger.info(f"Plan overridden to: {args.plan}")
    
    # Get auth mode
    auth_mode = os.getenv("X_AUTH_MODE", config.get("auth_mode", "tweepy"))
    logger.debug(f"Auth mode: {auth_mode}")
    
    # Import modules
    from auth import UnifiedAuth
    from budget import BudgetManager
    from storage import Storage
    from x_client import XClient
    
    # Initialize storage
    storage = Storage()
    
    # Handle OAuth 2.0 authorization
    if args.authorize:
        if auth_mode != "oauth2":
            logger.error("--authorize requires X_AUTH_MODE=oauth2")
            print("❌ --authorize requires X_AUTH_MODE=oauth2")
            sys.exit(1)
        
        logger.info("Starting OAuth 2.0 PKCE authorization flow...")
        print("\n🔐 Starting OAuth 2.0 PKCE authorization flow...")
        auth = UnifiedAuth.from_env("oauth2")  # type: ignore
        success = auth.authorize_oauth2()
        
        if success:
            logger.info("Authorization successful! Token saved.")
            print("✓ Authorization successful! Token saved.")
            sys.exit(0)
        else:
            logger.error("Authorization failed")
            print("❌ Authorization failed")
            sys.exit(1)
    
    # Initialize client
    try:
        logger.debug(f"Initializing client (dry_run={args.dry_run})")
        client = XClient.from_env(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}", exc_info=True)
        print(f"❌ Failed to initialize client: {e}")
        if auth_mode == "oauth2":
            print("\n💡 If using OAuth 2.0, run with --authorize first")
        sys.exit(1)
    
    # Handle safety/diagnostic commands
    if args.safety:
        if args.safety == "print-budget":
            budget_mgr = BudgetManager.from_config(config, storage=storage)
            budget_mgr.print_budget()
        elif args.safety == "print-limits":
            from rate_limiter import RateLimiter
            rate_limiter = RateLimiter()
            rate_limiter.print_limits()
        elif args.safety == "print-learning":
            from learn import print_bandit_stats
            print_bandit_stats(storage)
        sys.exit(0)
    
    # Handle learning operations
    if args.settle:
        from learn import settle
        from budget import BudgetManager
        
        logger.info(f"Fetching metrics for post: {args.settle}")
        print(f"\n📊 Fetching metrics for post: {args.settle}")
        
        # Determine arm (topic|slot|media)
        actions = storage.get_recent_actions(kind="post", limit=1)
        arm = "default|morning|False"  # Default
        for action in actions:
            if action.get("post_id") == args.settle:
                topic = action.get("topic", "default")
                slot = action.get("slot", "morning")
                media = action.get("media", 0)
                arm = f"{topic}|{slot}|{int(media) > 0}"
                break
        
        try:
            settle(client, storage, args.settle, arm)
            logger.info("Metrics settled successfully")
            print("✓ Metrics settled successfully")
        except Exception as e:
            logger.error(f"Failed to settle: {e}", exc_info=True)
            print(f"❌ Failed to settle: {e}")
            sys.exit(1)
        sys.exit(0)
    
    if args.settle_all:
        from learn import settle_all
        
        logger.info("Settling all owned posts...")
        print("\n📊 Settling all owned posts...")
        count = settle_all(client, storage, default_arm="default|morning|False")
        logger.info(f"Settled {count} posts")
        print(f"✓ Settled {count} posts")
        sys.exit(0)
    
    # Run main scheduler
    from scheduler import run_scheduler
    
    try:
        logger.info(f"Starting scheduler (mode={args.mode}, dry_run={args.dry_run})")
        run_scheduler(
            client=client,
            storage=storage,
            config=config,
            mode=args.mode,
            dry_run=args.dry_run,
        )
        logger.info("Scheduler completed successfully")
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in scheduler: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        storage.close()
        logger.debug("Storage connection closed")


if __name__ == "__main__":
    main()
