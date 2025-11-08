"""Tests for scheduler compatibility shim."""

from unittest.mock import MagicMock

import scheduler


def test_scheduler_shim_exports():
    # Ensure legacy import path still works
    assert hasattr(scheduler, "run_scheduler")
    assert hasattr(scheduler, "run_post_action")
    assert hasattr(scheduler, "run_interact_actions")
    assert hasattr(scheduler, "current_slot")


def test_scheduler_shim_dry_run_calls_get_me():
    """Test that dry-run path in scheduler shim calls client.get_me() for user ID filtering."""
    # Create mock client with get_me method
    mock_client = MagicMock()
    mock_client.get_me.return_value = {"data": {"id": "test-user-123"}}

    # Create mock storage
    mock_storage = MagicMock()

    # Config with queries
    config = {
        "queries": [{"query": "test query"}],
        "max_per_window": {"reply": 1, "like": 1, "follow": 1, "repost": 1},
        "jitter_seconds": [1, 2],
    }

    # Call run_interact_actions in dry-run mode
    scheduler.run_interact_actions(mock_client, mock_storage, config, dry_run=True)

    # Verify get_me was called to fetch authenticated user ID
    mock_client.get_me.assert_called_once()

