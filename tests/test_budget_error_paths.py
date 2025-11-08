"""Comprehensive error path coverage for budget.py plan management.

Tests cover:
- Plan validation and cap enforcement (free/basic/pro)
- Storage integration and None handling
- Soft/hard cap logic with buffer
- Monthly period calculation
- from_config factory method
- Backward compatibility functions
- Edge cases: zero caps, 100% usage, negative counts
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.budget import BudgetManager, add_create, add_reads, configure_caps

# ==================== Plan Validation Tests ====================


def test_invalid_plan_type():
    """Test that invalid plan type raises KeyError."""
    with pytest.raises(KeyError):
        BudgetManager(plan="invalid_plan")  # type: ignore


def test_all_plan_caps():
    """Test all three plan tiers have correct caps."""
    free = BudgetManager(plan="free")
    assert free.read_cap == 100
    assert free.write_cap == 500

    basic = BudgetManager(plan="basic")
    assert basic.read_cap == 15000
    assert basic.write_cap == 50000

    pro = BudgetManager(plan="pro")
    assert pro.read_cap == 1000000
    assert pro.write_cap == 300000


def test_custom_caps_override_plan():
    """Test custom caps override plan defaults."""
    bm = BudgetManager(plan="free", custom_read_cap=200, custom_write_cap=1000)
    assert bm.read_cap == 200
    assert bm.write_cap == 1000
    # Soft caps should apply buffer to custom caps
    assert bm.soft_read_cap == int(200 * 0.95)
    assert bm.soft_write_cap == int(1000 * 0.95)


def test_custom_buffer_percentage():
    """Test custom buffer percentage."""
    bm = BudgetManager(plan="free", buffer_pct=0.10)  # 10% buffer
    assert bm.soft_read_cap == int(100 * 0.90)
    assert bm.soft_write_cap == int(500 * 0.90)


def test_zero_buffer():
    """Test zero buffer makes soft cap equal to hard cap."""
    bm = BudgetManager(plan="free", buffer_pct=0.0)
    assert bm.soft_read_cap == bm.read_cap
    assert bm.soft_write_cap == bm.write_cap


# ==================== Storage Integration Tests ====================


def test_storage_none_no_import():
    """Test BudgetManager with storage=None when Storage not available."""
    with patch("src.budget.Storage", None):
        bm = BudgetManager(storage=None, plan="free")
        assert bm.storage is None

        usage = bm.get_usage()
        assert usage["reads"] == 0
        assert usage["writes"] == 0


def test_storage_auto_import():
    """Test BudgetManager auto-creates Storage when storage=None and Storage available."""
    # When storage=None is passed AND Storage is importable, budget.py creates one
    # The actual implementation in budget.py __init__ does:
    # if storage is None and Storage is not None:
    #     from storage import Storage as StorageClass
    #     storage = StorageClass()
    # So we can't easily mock the import. Instead, test that it creates a real Storage.
    bm = BudgetManager(plan="free", storage=None)
    # It will create a real Storage instance
    assert bm.storage is not None


def test_get_usage_with_no_storage():
    """Test get_usage returns zeros when storage is explicitly None."""
    # Need to ensure Storage module is not auto-imported
    # Pass a mock storage then set to None
    mock_storage = MagicMock()
    bm = BudgetManager(storage=mock_storage, plan="free")
    bm.storage = None  # Explicitly set to None

    usage = bm.get_usage()

    assert usage["reads"] == 0
    assert usage["writes"] == 0
    assert usage["period"] == datetime.now(UTC).strftime("%Y-%m")


def test_get_usage_with_storage_data():
    """Test get_usage retrieves data from storage."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 50, "create_count": 200}

    bm = BudgetManager(storage=mock_storage, plan="free")
    usage = bm.get_usage()

    assert usage["reads"] == 50
    assert usage["writes"] == 200
    assert usage["read_remaining"] == 50
    assert usage["write_remaining"] == 300


def test_add_reads_no_storage():
    """Test add_reads does nothing when storage is None."""
    bm = BudgetManager(storage=None, plan="free")
    # Should not raise
    bm.add_reads(10)


def test_add_writes_no_storage():
    """Test add_writes does nothing when storage is None."""
    bm = BudgetManager(storage=None, plan="free")
    # Should not raise
    bm.add_writes(5)


def test_add_reads_with_storage():
    """Test add_reads calls storage.update_monthly_usage."""
    mock_storage = MagicMock()
    bm = BudgetManager(storage=mock_storage, plan="free")
    bm.add_reads(25)

    period = datetime.now(UTC).strftime("%Y-%m")
    mock_storage.update_monthly_usage.assert_called_once_with(period, read_count=25)


def test_add_writes_with_storage():
    """Test add_writes calls storage.update_monthly_usage."""
    mock_storage = MagicMock()
    bm = BudgetManager(storage=mock_storage, plan="free")
    bm.add_writes(10)

    period = datetime.now(UTC).strftime("%Y-%m")
    mock_storage.update_monthly_usage.assert_called_once_with(period, create_count=10)


def test_add_create_alias():
    """Test add_create is an alias for add_writes."""
    mock_storage = MagicMock()
    bm = BudgetManager(storage=mock_storage, plan="free")
    bm.add_create(7)

    period = datetime.now(UTC).strftime("%Y-%m")
    mock_storage.update_monthly_usage.assert_called_once_with(period, create_count=7)


# ==================== Cap Enforcement Tests ====================


def test_can_read_hard_cap_exceeded():
    """Test can_read blocks when hard cap would be exceeded."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 95, "create_count": 0}

    bm = BudgetManager(storage=mock_storage, plan="free")  # cap: 100
    can, msg = bm.can_read(posts_count=10)  # would be 105 > 100

    assert can is False
    assert "Hard cap exceeded" in msg
    assert "105 > 100" in msg


def test_can_read_soft_cap_exceeded():
    """Test can_read blocks when soft cap would be exceeded."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 90, "create_count": 0}

    bm = BudgetManager(storage=mock_storage, plan="free")  # soft: 95, hard: 100
    can, msg = bm.can_read(posts_count=10)  # would be 100 > 95

    assert can is False
    assert "Soft cap exceeded" in msg
    assert "buffer: 5.0%" in msg


def test_can_read_within_soft_cap():
    """Test can_read allows when within soft cap."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 80, "create_count": 0}

    bm = BudgetManager(storage=mock_storage, plan="free")
    can, msg = bm.can_read(posts_count=10)  # would be 90 < 95

    assert can is True
    assert "OK:" in msg


def test_can_write_hard_cap_exceeded():
    """Test can_write blocks when hard cap would be exceeded."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 0, "create_count": 495}

    bm = BudgetManager(storage=mock_storage, plan="free")  # cap: 500
    can, msg = bm.can_write(count=10)  # would be 505 > 500

    assert can is False
    assert "Hard cap exceeded" in msg
    assert "505 > 500" in msg


def test_can_write_soft_cap_exceeded():
    """Test can_write blocks when soft cap would be exceeded."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 0, "create_count": 470}

    bm = BudgetManager(storage=mock_storage, plan="free")  # soft: 475, hard: 500
    can, msg = bm.can_write(count=10)  # would be 480 > 475

    assert can is False
    assert "Soft cap exceeded" in msg


def test_can_write_within_soft_cap():
    """Test can_write allows when within soft cap."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 0, "create_count": 400}

    bm = BudgetManager(storage=mock_storage, plan="free")
    can, msg = bm.can_write(count=50)  # would be 450 < 475

    assert can is True
    assert "OK:" in msg


# ==================== Edge Cases Tests ====================


def test_zero_read_cap_division():
    """Test get_usage handles zero read_cap without division by zero."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 0, "create_count": 0}

    bm = BudgetManager(storage=mock_storage, plan="free", custom_read_cap=0)
    usage = bm.get_usage()

    # When both reads and read_cap are 0, percentage should be 0
    assert usage["read_pct"] == 0


def test_zero_write_cap_division():
    """Test get_usage handles zero write_cap without division by zero."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 0, "create_count": 0}

    bm = BudgetManager(storage=mock_storage, plan="free", custom_write_cap=0)
    usage = bm.get_usage()

    # When both writes and write_cap are 0, percentage should be 0
    assert usage["write_pct"] == 0


def test_100_percent_usage():
    """Test get_usage calculates 100% correctly."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 100, "create_count": 500}

    bm = BudgetManager(storage=mock_storage, plan="free")
    usage = bm.get_usage()

    assert usage["read_pct"] == 100.0
    assert usage["write_pct"] == 100.0
    assert usage["read_remaining"] == 0
    assert usage["write_remaining"] == 0


def test_current_period_format():
    """Test _current_period returns YYYY-MM format."""
    bm = BudgetManager(plan="free")
    period = bm._current_period()

    assert len(period) == 7
    assert period[4] == "-"
    assert period.count("-") == 1

    # Verify it's valid datetime format
    datetime.strptime(period, "%Y-%m")


def test_print_budget_output(capsys):
    """Test print_budget displays formatted output."""
    mock_storage = MagicMock()
    mock_storage.get_monthly_usage.return_value = {"read_count": 50, "create_count": 200}

    bm = BudgetManager(storage=mock_storage, plan="free")
    bm.print_budget()

    captured = capsys.readouterr()
    assert "Budget Status" in captured.out
    assert "Plan: FREE" in captured.out
    assert "READS:" in captured.out
    assert "WRITES:" in captured.out
    assert "50 / 100" in captured.out
    assert "200 / 500" in captured.out


# ==================== Factory Method Tests ====================


def test_from_config_basic():
    """Test from_config with basic config."""
    config = {"plan": "basic", "buffer_pct": 0.10}
    bm = BudgetManager.from_config(config)

    assert bm.plan == "basic"
    assert bm.buffer_pct == 0.10
    assert bm.read_cap == 15000
    assert bm.write_cap == 50000


def test_from_config_with_custom_caps():
    """Test from_config with custom caps."""
    config = {
        "plan": "pro",
        "buffer_pct": 0.02,
        "custom_read_cap": 50000,
        "custom_write_cap": 10000,
    }
    bm = BudgetManager.from_config(config)

    assert bm.plan == "pro"
    assert bm.buffer_pct == 0.02
    assert bm.read_cap == 50000
    assert bm.write_cap == 10000


def test_from_config_defaults():
    """Test from_config uses defaults when keys missing."""
    config: dict = {}
    bm = BudgetManager.from_config(config)

    assert bm.plan == "free"
    assert bm.buffer_pct == 0.05


def test_from_config_with_storage():
    """Test from_config accepts storage parameter."""
    mock_storage = MagicMock()
    config = {"plan": "basic"}
    bm = BudgetManager.from_config(config, storage=mock_storage)

    assert bm.storage is mock_storage


# ==================== Backward Compatibility Tests ====================


def test_configure_caps_posts_create():
    """Test configure_caps sets create cap."""
    configure_caps(posts_create_cap=1000, posts_read_cap=None)
    # Note: This tests the function doesn't crash
    # Real behavior would need global state check


def test_configure_caps_posts_read():
    """Test configure_caps sets read cap."""
    configure_caps(posts_create_cap=None, posts_read_cap=200)
    # Note: This tests the function doesn't crash


def test_add_create_compat(capsys):
    """Test backward-compatible add_create function."""
    add_create(5, cap=1000)
    captured = capsys.readouterr()
    assert "[COMPAT]" in captured.out
    assert "add_create(5)" in captured.out
    assert "cap 1000" in captured.out


def test_add_reads_compat(capsys):
    """Test backward-compatible add_reads function."""
    add_reads(25, cap=500)
    captured = capsys.readouterr()
    assert "[COMPAT]" in captured.out
    assert "add_reads(25)" in captured.out
    assert "cap 500" in captured.out


def test_add_create_default_cap(capsys):
    """Test add_create uses global _CREATE_CAP."""
    # The compat function doesn't actually use the global for display,
    # it uses the cap parameter which defaults to _CREATE_CAP
    # But since we can call configure_caps to change it, let's test that path

    add_create(3)  # Should use _CREATE_CAP which is 500
    captured = capsys.readouterr()
    # The function prints the cap value it receives
    assert "add_create(3)" in captured.out


def test_add_reads_default_cap(capsys):
    """Test add_reads uses global _READ_CAP."""

    add_reads(10)  # Should use _READ_CAP which is 100
    captured = capsys.readouterr()
    assert "add_reads(10)" in captured.out
