"""Main CLI entry point for X Agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auth import XAuth
from budget import BudgetManager
from scheduler import Scheduler
from storage import Storage
from x_client import XClient


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="X Agent - Production-ready, compliant autonomous X (Twitter) agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--mode",
        choices=["post", "interact", "both", "settle-metrics"],
        default="both",
        help="Execution mode",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no actual API calls)",
    )
    
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file",
    )
    
    parser.add_argument(
        "--db",
        default="data/x_agent.db",
        help="Path to SQLite database",
    )
    
    parser.add_argument(
        "--plan",
        choices=["free", "basic", "pro"],
        default="free",
        help="X API plan tier",
    )
    
    parser.add_argument(
        "--safety",
        choices=["print-limits", "print-budget"],
        help="Print safety information",
    )
    
    parser.add_argument(
        "--authorize",
        action="store_true",
        help="Run OAuth authorization flow",
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Initialize storage
    storage = Storage(args.db)
    budget = BudgetManager(storage, plan=args.plan)
    
    # Handle safety commands
    if args.safety:
        if args.safety == "print-budget":
            budget.print_budget()
            return 0
        elif args.safety == "print-limits":
            # Need to initialize client first
            client = XClient.from_env(budget, dry_run=True)
            client.rate_limiter.print_limits()
            return 0
    
    # Handle authorization
    if args.authorize:
        print("=== Starting OAuth 2.0 Authorization ===")
        auth = XAuth.from_env()
        scopes = [
            "tweet.read",
            "tweet.write",
            "users.read",
            "offline.access",
            "like.read",
            "like.write",
            "follows.read",
            "follows.write",
        ]
        
        try:
            token = auth.authorize(scopes)
            print(f"\n✓ Authorization successful!")
            print(f"Access token saved. You can now run the agent.")
            return 0
        except Exception as e:
            print(f"\n❌ Authorization failed: {e}")
            return 1
    
    # Check config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print(f"   Copy config.example.yaml to {args.config} and customize it.")
        return 1
    
    # Initialize client
    try:
        client = XClient.from_env(budget, dry_run=args.dry_run)
        
        # Verify auth
        if not args.dry_run:
            me = client.get_me()
            username = me.get("data", {}).get("username", "unknown")
            print(f"\n✓ Authenticated as @{username}")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print(f"   Run with --authorize to obtain access token")
        return 1
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No actual API calls will be made\n")
    
    # Initialize scheduler
    scheduler = Scheduler.from_config(args.config, client, storage, budget)
    
    # Execute based on mode
    try:
        if args.mode == "post":
            scheduler.run_post_actions()
        
        elif args.mode == "interact":
            scheduler.run_interact_actions()
        
        elif args.mode == "both":
            scheduler.run_post_actions()
            print()  # Spacing
            scheduler.run_interact_actions()
        
        elif args.mode == "settle-metrics":
            scheduler.settle_metrics()
        
        # Print budget summary
        print()
        budget.print_budget()
        
        # Print rate limits if not dry run
        if not args.dry_run:
            client.rate_limiter.print_limits()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        storage.close()


if __name__ == "__main__":
    sys.exit(main())
