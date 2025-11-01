"""Smoke tests for X Agent core components."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from budget import BudgetManager
from storage import Storage
from x_client import XClient


def test_storage():
    """Test storage initialization and operations."""
    print("\n=== Testing Storage ===")
    
    db_path = "data/test_smoke.db"
    storage = Storage(db_path)
    
    # Test action logging
    action_id = storage.log_action(
        kind="test_action",
        post_id="test123",
        text="Test post",
        status="success",
    )
    print(f"✓ Logged action: {action_id}")
    
    # Test duplicate detection
    is_dup = storage.is_text_duplicate("Test post")
    print(f"✓ Duplicate detection: {is_dup}")
    
    # Test metrics
    storage.update_metrics("test123", like_count=5, reply_count=2)
    metrics = storage.get_metrics("test123")
    print(f"✓ Metrics stored: {metrics}")
    
    # Test usage tracking
    storage.update_monthly_usage("2025-11", create_count=1, read_count=5)
    usage = storage.get_monthly_usage("2025-11")
    print(f"✓ Usage tracking: {usage}")
    
    storage.close()
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✓ Storage tests passed")


def test_budget():
    """Test budget manager."""
    print("\n=== Testing Budget Manager ===")
    
    db_path = "data/test_budget.db"
    storage = Storage(db_path)
    budget = BudgetManager(storage, plan="free")
    
    # Test budget checks
    can_read, msg = budget.can_read(10)
    print(f"✓ Read check: {can_read} - {msg}")
    
    can_write, msg = budget.can_write(1)
    print(f"✓ Write check: {can_write} - {msg}")
    
    # Test tracking
    budget.add_reads(5)
    budget.add_writes(1)
    
    usage = budget.get_usage()
    print(f"✓ Usage: {usage['reads']} reads, {usage['writes']} writes")
    
    # Print budget
    budget.print_budget()
    
    storage.close()
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✓ Budget tests passed")


def test_dry_run_client():
    """Test X client in dry-run mode."""
    print("\n=== Testing X Client (Dry Run) ===")
    
    db_path = "data/test_client.db"
    storage = Storage(db_path)
    budget = BudgetManager(storage, plan="free")
    
    # Create client in dry-run mode
    client = XClient.from_env(budget, dry_run=True)
    
    # Test endpoints
    print("\nTesting endpoints:")
    
    result = client.get_me()
    print(f"✓ get_me: {result}")
    
    result = client.create_post("Test post from dry run")
    print(f"✓ create_post: {result}")
    
    result = client.search_recent("test query", max_results=5)
    print(f"✓ search_recent: {result}")
    
    result = client.like_post("user123", "post123")
    print(f"✓ like_post: {result}")
    
    storage.close()
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✓ Client dry-run tests passed")


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("X Agent Smoke Tests")
    print("=" * 60)
    
    try:
        test_storage()
        test_budget()
        test_dry_run_client()
        
        print("\n" + "=" * 60)
        print("✅ All smoke tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
