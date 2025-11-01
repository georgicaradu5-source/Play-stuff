"""Live test for X Agent (requires valid credentials and --confirm flag)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from budget import BudgetManager
from storage import Storage
from x_client import XClient


def main():
    """Run live test with confirmation."""
    parser = argparse.ArgumentParser(description="X Agent Live Test")
    parser.add_argument("--confirm", action="store_true", help="Confirm live API call")
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  This test makes REAL API calls to X (Twitter).")
        print("   It will create one post and consume budget.")
        print("\n   Run with --confirm flag to proceed:")
        print("   python tests/live_test.py --confirm")
        return 1
    
    print("\n=== X Agent Live Test ===")
    print("This will create ONE test post on your X account.\n")
    
    # Initialize
    storage = Storage("data/test_live.db")
    budget = BudgetManager(storage, plan="free")
    
    try:
        # Create client
        client = XClient.from_env(budget, dry_run=False)
        
        # Get authenticated user
        print("1. Getting authenticated user...")
        me = client.get_me()
        username = me.get("data", {}).get("username", "unknown")
        print(f"   ✓ Authenticated as @{username}")
        
        # Check budget
        print("\n2. Checking budget...")
        budget.print_budget()
        can_write, msg = budget.can_write(1)
        if not can_write:
            print(f"   ❌ Cannot write: {msg}")
            return 1
        print(f"   ✓ Budget OK")
        
        # Create test post
        print("\n3. Creating test post...")
        test_text = "🤖 Test post from X Agent - Production-ready autonomous agent testing. #automation"
        
        result = client.create_post(test_text)
        post_id = result.get("data", {}).get("id")
        print(f"   ✓ Post created: {post_id}")
        print(f"   Text: {test_text}")
        
        # Log to storage
        storage.log_action(
            kind="live_test_post",
            post_id=post_id,
            text=test_text,
            status="success",
        )
        
        # Print updated budget
        print("\n4. Updated budget:")
        budget.print_budget()
        
        # Print rate limits
        print("\n5. Rate limit status:")
        client.rate_limiter.print_limits()
        
        print("\n✅ Live test successful!")
        print(f"\n   View your post: https://twitter.com/{username}/status/{post_id}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Live test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        storage.close()


if __name__ == "__main__":
    sys.exit(main())
