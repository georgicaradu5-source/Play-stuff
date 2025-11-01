"""Budget manager for monthly READ/WRITE caps."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from storage import Storage


PlanType = Literal["free", "basic", "pro"]


class BudgetManager:
    """Manage monthly API usage budgets."""

    # Plan caps (monthly)
    PLAN_CAPS = {
        "free": {"reads": 100, "writes": 500},
        "basic": {"reads": 15000, "writes": 50000},
        "pro": {"reads": 1000000, "writes": 300000},
    }

    def __init__(self, storage: Storage, plan: PlanType = "free", buffer_pct: float = 0.05):
        self.storage = storage
        self.plan = plan
        self.buffer_pct = buffer_pct
        self.caps = self.PLAN_CAPS[plan]
        
        # Apply safety buffer
        self.soft_read_cap = int(self.caps["reads"] * (1 - buffer_pct))
        self.soft_write_cap = int(self.caps["writes"] * (1 - buffer_pct))

    def _current_period(self) -> str:
        """Get current month period (YYYY-MM)."""
        return datetime.utcnow().strftime("%Y-%m")

    def get_usage(self) -> dict:
        """Get current month usage."""
        period = self._current_period()
        usage = self.storage.get_monthly_usage(period)
        return {
            "period": period,
            "plan": self.plan,
            "reads": usage["read_count"],
            "writes": usage["create_count"],
            "read_cap": self.caps["reads"],
            "write_cap": self.caps["writes"],
            "read_remaining": self.caps["reads"] - usage["read_count"],
            "write_remaining": self.caps["writes"] - usage["create_count"],
            "read_pct": (usage["read_count"] / self.caps["reads"]) * 100,
            "write_pct": (usage["create_count"] / self.caps["writes"]) * 100,
        }

    def can_read(self, posts_count: int = 1) -> tuple[bool, str]:
        """Check if READ operation is within budget."""
        usage = self.get_usage()
        new_total = usage["reads"] + posts_count
        
        if new_total > self.caps["reads"]:
            return False, f"Hard cap exceeded: {new_total} > {self.caps['reads']}"
        
        if new_total > self.soft_read_cap:
            return False, f"Soft cap exceeded: {new_total} > {self.soft_read_cap} (buffer: {self.buffer_pct*100}%)"
        
        return True, f"OK: {new_total}/{self.soft_read_cap} reads"

    def can_write(self, count: int = 1) -> tuple[bool, str]:
        """Check if WRITE operation is within budget."""
        usage = self.get_usage()
        new_total = usage["writes"] + count
        
        if new_total > self.caps["writes"]:
            return False, f"Hard cap exceeded: {new_total} > {self.caps['writes']}"
        
        if new_total > self.soft_write_cap:
            return False, f"Soft cap exceeded: {new_total} > {self.soft_write_cap} (buffer: {self.buffer_pct*100}%)"
        
        return True, f"OK: {new_total}/{self.soft_write_cap} writes"

    def add_reads(self, posts_count: int) -> None:
        """Record READ operations (posts returned from API)."""
        period = self._current_period()
        self.storage.update_monthly_usage(period, read_count=posts_count)

    def add_writes(self, count: int = 1) -> None:
        """Record WRITE operations (creates/deletes)."""
        period = self._current_period()
        self.storage.update_monthly_usage(period, create_count=count)

    def print_budget(self) -> None:
        """Print current budget status."""
        usage = self.get_usage()
        print(f"\n=== Budget Status ({usage['period']}) ===")
        print(f"Plan: {usage['plan'].upper()}")
        print(f"\nREADS:  {usage['reads']:,} / {usage['read_cap']:,} ({usage['read_pct']:.1f}%)")
        print(f"  Remaining: {usage['read_remaining']:,}")
        print(f"\nWRITES: {usage['writes']:,} / {usage['write_cap']:,} ({usage['write_pct']:.1f}%)")
        print(f"  Remaining: {usage['write_remaining']:,}")
        
        # Warnings
        if usage['read_pct'] > 80:
            print(f"\n⚠️  WARNING: Read usage above 80%")
        if usage['write_pct'] > 80:
            print(f"\n⚠️  WARNING: Write usage above 80%")
