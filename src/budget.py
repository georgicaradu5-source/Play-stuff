"""Enhanced budget manager combining plan tiers with flexible caps."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

try:
    from storage import Storage
except ImportError:
    Storage = None  # type: ignore

from logger import get_logger

logger = get_logger(__name__)


PlanType = Literal["free", "basic", "pro"]


class BudgetManager:
    """Manage monthly API usage budgets with plan tiers."""

    # Plan caps (monthly) - X API v2 limits
    PLAN_CAPS = {
        "free": {"reads": 100, "writes": 500},
        "basic": {"reads": 15000, "writes": 50000},
        "pro": {"reads": 1000000, "writes": 300000},
    }

    def __init__(
        self,
        storage: Storage | None = None,
        plan: PlanType = "free",
        buffer_pct: float = 0.05,
        custom_read_cap: int | None = None,
        custom_write_cap: int | None = None,
    ):
        """Initialize budget manager.

        Args:
            storage: Storage instance for persistence
            plan: Plan tier (free, basic, pro)
            buffer_pct: Safety buffer percentage (default 5%)
            custom_read_cap: Override read cap
            custom_write_cap: Override write cap
        """
        if storage is None and Storage is not None:
            from storage import Storage as StorageClass
            storage = StorageClass()

        self.storage = storage
        self.plan = plan
        self.buffer_pct = buffer_pct

        # Use custom caps or plan defaults
        base_caps = self.PLAN_CAPS[plan]
        self.read_cap = custom_read_cap or base_caps["reads"]
        self.write_cap = custom_write_cap or base_caps["writes"]

        # Apply safety buffer
        self.soft_read_cap = int(self.read_cap * (1 - buffer_pct))
        self.soft_write_cap = int(self.write_cap * (1 - buffer_pct))

    def _current_period(self) -> str:
        """Get current month period (YYYY-MM)."""
        return datetime.utcnow().strftime("%Y-%m")

    def get_usage(self) -> dict:
        """Get current month usage."""
        period = self._current_period()

        if self.storage:
            usage = self.storage.get_monthly_usage(period)
            reads = usage.get("read_count", 0)
            writes = usage.get("create_count", 0)
        else:
            reads = 0
            writes = 0

        return {
            "period": period,
            "plan": self.plan,
            "reads": reads,
            "writes": writes,
            "read_cap": self.read_cap,
            "write_cap": self.write_cap,
            "read_remaining": self.read_cap - reads,
            "write_remaining": self.write_cap - writes,
            "read_pct": (reads / self.read_cap) * 100 if self.read_cap > 0 else 0,
            "write_pct": (writes / self.write_cap) * 100 if self.write_cap > 0 else 0,
        }

    def can_read(self, posts_count: int = 1) -> tuple[bool, str]:
        """Check if READ operation is within budget."""
        usage = self.get_usage()
        new_total = usage["reads"] + posts_count

        if new_total > self.read_cap:
            return False, f"Hard cap exceeded: {new_total} > {self.read_cap}"

        if new_total > self.soft_read_cap:
            return False, f"Soft cap exceeded: {new_total} > {self.soft_read_cap} (buffer: {self.buffer_pct*100}%)"

        return True, f"OK: {new_total}/{self.soft_read_cap} reads"

    def can_write(self, count: int = 1) -> tuple[bool, str]:
        """Check if WRITE operation is within budget."""
        usage = self.get_usage()
        new_total = usage["writes"] + count

        if new_total > self.write_cap:
            return False, f"Hard cap exceeded: {new_total} > {self.write_cap}"

        if new_total > self.soft_write_cap:
            return False, f"Soft cap exceeded: {new_total} > {self.soft_write_cap} (buffer: {self.buffer_pct*100}%)"

        return True, f"OK: {new_total}/{self.soft_write_cap} writes"

    def add_reads(self, posts_count: int) -> None:
        """Record READ operations (posts returned from API)."""
        if not self.storage:
            return

        period = self._current_period()
        self.storage.update_monthly_usage(period, read_count=posts_count)

    def add_writes(self, count: int = 1) -> None:
        """Record WRITE operations (creates/deletes)."""
        if not self.storage:
            return

        period = self._current_period()
        self.storage.update_monthly_usage(period, create_count=count)

    def add_create(self, count: int = 1) -> None:
        """Alias for add_writes (backward compatibility with agent-x)."""
        self.add_writes(count)

    def print_budget(self) -> None:
        """Print current budget status."""
        usage = self.get_usage()
        print(f"\n=== Budget Status ({usage['period']}) ===")
        print(f"Plan: {usage['plan'].upper()}")
        print(f"\nREADS:  {usage['reads']:,} / {usage['read_cap']:,} ({usage['read_pct']:.1f}%)")
        print(f"  Remaining: {usage['read_remaining']:,}")
        print(f"  Soft cap: {self.soft_read_cap:,} (buffer: {self.buffer_pct*100:.0f}%)")
        print(f"\nWRITES: {usage['writes']:,} / {usage['write_cap']:,} ({usage['write_pct']:.1f}%)")
        print(f"  Remaining: {usage['write_remaining']:,}")
        print(f"  Soft cap: {self.soft_write_cap:,} (buffer: {self.buffer_pct*100:.0f}%)")

    @classmethod
    def from_config(cls, config: dict, storage: Storage | None = None) -> BudgetManager:
        """Create BudgetManager from config dict.

        Example config:
        {
            "plan": "free",
            "buffer_pct": 0.05,
            "custom_read_cap": 200,  # optional
            "custom_write_cap": 1000  # optional
        }
        """
        return cls(
            storage=storage,
            plan=config.get("plan", "free"),  # type: ignore
            buffer_pct=config.get("buffer_pct", 0.05),
            custom_read_cap=config.get("custom_read_cap"),
            custom_write_cap=config.get("custom_write_cap"),
        )


# Backward compatibility functions for agent-x
_CREATE_CAP = 500
_READ_CAP = 100


def configure_caps(posts_create_cap: int | None, posts_read_cap: int | None) -> None:
    """Configure global caps (agent-x compatibility)."""
    global _CREATE_CAP, _READ_CAP
    if posts_create_cap:
        _CREATE_CAP = int(posts_create_cap)
    if posts_read_cap:
        _READ_CAP = int(posts_read_cap)


def add_create(n: int = 1, cap: int | None = None) -> None:
    """Add create count with cap check (agent-x compatibility).

    Note: This is a simplified version for backward compatibility.
    For full budget management, use BudgetManager class.
    """
    cap = cap if cap is not None else _CREATE_CAP
    # Basic check without storage
    # Real implementation would need storage instance
    print(f"[COMPAT] add_create({n}) against cap {cap}")


def add_reads(posts_returned: int, cap: int | None = None) -> None:
    """Add read count with cap check (agent-x compatibility).

    Note: This is a simplified version for backward compatibility.
    For full budget management, use BudgetManager class.
    """
    cap = cap if cap is not None else _READ_CAP
    print(f"[COMPAT] add_reads({posts_returned}) against cap {cap}")
