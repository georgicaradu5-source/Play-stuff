"""Comprehensive coverage for rate_limiter.py backoff and rate tracking.

Tests cover:
- Header parsing and rate limit tracking
- can_call logic with safety thresholds
- wait_if_needed blocking behavior
- Exponential backoff with jitter
- backoff_and_retry error handling
- Rate limit exhaustion scenarios
- Edge cases: missing headers, expired windows
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from src.rate_limiter import RateLimiter


# ==================== Header Parsing Tests ====================


def test_update_from_headers_all_present():
    """Test update_from_headers stores rate limit info."""
    rl = RateLimiter()
    headers = {
        "x-rate-limit-limit": "15",
        "x-rate-limit-remaining": "10",
        "x-rate-limit-reset": str(int(time.time()) + 900),
    }

    rl.update_from_headers("test_endpoint", headers)

    assert "test_endpoint" in rl.limits
    assert rl.limits["test_endpoint"]["limit"] == 15
    assert rl.limits["test_endpoint"]["remaining"] == 10
    assert "reset" in rl.limits["test_endpoint"]


def test_update_from_headers_case_insensitive():
    """Test headers work with uppercase keys."""
    rl = RateLimiter()
    headers = {
        "X-Rate-Limit-Limit": "20",
        "X-Rate-Limit-Remaining": "5",
        "X-Rate-Limit-Reset": str(int(time.time()) + 600),
    }

    rl.update_from_headers("test_endpoint", headers)

    assert rl.limits["test_endpoint"]["limit"] == 20
    assert rl.limits["test_endpoint"]["remaining"] == 5


def test_update_from_headers_missing_headers():
    """Test update_from_headers does nothing when headers missing."""
    rl = RateLimiter()
    headers = {"x-rate-limit-limit": "10"}  # Missing remaining and reset

    rl.update_from_headers("test_endpoint", headers)

    # Should not add endpoint if incomplete
    assert "test_endpoint" not in rl.limits


def test_update_from_headers_updated_at():
    """Test update_from_headers sets updated_at timestamp."""
    rl = RateLimiter()
    headers = {
        "x-rate-limit-limit": "10",
        "x-rate-limit-remaining": "5",
        "x-rate-limit-reset": str(int(time.time()) + 300),
    }

    before = time.time()
    rl.update_from_headers("endpoint", headers)
    after = time.time()

    assert "updated_at" in rl.limits["endpoint"]
    updated = rl.limits["endpoint"]["updated_at"]
    assert before <= updated <= after


# ==================== can_call Tests ====================


def test_can_call_no_limit_info():
    """Test can_call returns True when endpoint not tracked."""
    rl = RateLimiter()

    can, wait = rl.can_call("unknown_endpoint")

    assert can is True
    assert wait is None


def test_can_call_above_threshold():
    """Test can_call allows when remaining above min_remaining."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 50,
        "reset": int(time.time()) + 600,
    }

    can, wait = rl.can_call("endpoint", min_remaining=5)

    assert can is True
    assert wait is None


def test_can_call_below_threshold():
    """Test can_call blocks when remaining below min_remaining."""
    rl = RateLimiter()
    reset_time = int(time.time()) + 300
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 3,
        "reset": reset_time,
    }

    can, wait = rl.can_call("endpoint", min_remaining=5)

    assert can is False
    assert wait is not None
    assert wait > 0


def test_can_call_exact_threshold():
    """Test can_call allows when remaining equals min_remaining (edge case)."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 5,
        "reset": int(time.time()) + 300,
    }

    can, wait = rl.can_call("endpoint", min_remaining=5)

    # remaining (5) < min_remaining (5) is False, so can_call should be True
    assert can is True
    assert wait is None


def test_can_call_expired_reset():
    """Test can_call when reset time has passed."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 2,
        "reset": int(time.time()) - 10,  # Already passed
    }

    can, wait = rl.can_call("endpoint", min_remaining=5)

    assert can is False
    assert wait == 0  # No need to wait, already expired


# ==================== wait_if_needed Tests ====================


def test_wait_if_needed_can_proceed():
    """Test wait_if_needed doesn't wait when rate limit OK."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 50,
        "reset": int(time.time()) + 600,
    }

    # Should return immediately
    start = time.time()
    rl.wait_if_needed("endpoint")
    duration = time.time() - start

    assert duration < 0.1  # No significant wait


def test_wait_if_needed_blocks(capsys):
    """Test wait_if_needed blocks when rate limit low."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 2,  # Below min_remaining of 5
        "reset": int(time.time()) + 2,  # 2 seconds wait
    }

    # Need to mock both logger.warning and time.sleep, plus print
    with patch("time.sleep") as mock_sleep, patch("src.rate_limiter.logger"):
        rl.wait_if_needed("endpoint", min_remaining=5)

        # Should have called sleep
        mock_sleep.assert_called_once()
        sleep_arg = mock_sleep.call_args[0][0]
        assert sleep_arg >= 2  # wait_seconds (2) + 1 buffer

    captured = capsys.readouterr()
    assert "WAIT" in captured.out or "Rate limit" in captured.out


# ==================== Jitter Tests ====================


def test_add_jitter_default_range():
    """Test add_jitter uses default range."""
    rl = RateLimiter()

    with patch("time.sleep") as mock_sleep:
        rl.add_jitter()

        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        # Default: 100-2000ms = 0.1-2.0s
        assert 0.1 <= delay <= 2.0


def test_add_jitter_custom_range():
    """Test add_jitter with custom min/max."""
    rl = RateLimiter()

    with patch("time.sleep") as mock_sleep:
        rl.add_jitter(min_ms=500, max_ms=1000)

        delay = mock_sleep.call_args[0][0]
        assert 0.5 <= delay <= 1.0


def test_add_jitter_randomness():
    """Test add_jitter produces different values."""
    rl = RateLimiter()
    delays = []

    with patch("time.sleep") as mock_sleep:
        for _ in range(10):
            rl.add_jitter()
            delays.append(mock_sleep.call_args[0][0])

    # At least some variance in delays
    assert len(set(delays)) > 1


# ==================== backoff_and_retry Tests ====================


def test_backoff_and_retry_success_first_attempt():
    """Test backoff_and_retry returns on first successful call."""
    rl = RateLimiter()
    mock_func = MagicMock(return_value="success")

    result = rl.backoff_and_retry(mock_func, "arg1", kwarg1="val1")

    assert result == "success"
    mock_func.assert_called_once_with("arg1", kwarg1="val1")


def test_backoff_and_retry_429_error():
    """Test backoff_and_retry retries on 429 error."""
    rl = RateLimiter()
    mock_func = MagicMock(side_effect=[Exception("429 Too Many Requests"), "success"])

    with patch("time.sleep") as mock_sleep:
        result = rl.backoff_and_retry(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()


def test_backoff_and_retry_rate_limit_text():
    """Test backoff_and_retry retries on 'rate limit' text."""
    rl = RateLimiter()
    mock_func = MagicMock(side_effect=[Exception("Rate Limit Exceeded"), "success"])

    with patch("time.sleep"):
        result = rl.backoff_and_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 2


def test_backoff_and_retry_exponential_backoff():
    """Test backoff_and_retry uses exponential backoff."""
    rl = RateLimiter()
    errors = [Exception("429"), Exception("429"), "success"]
    mock_func = MagicMock(side_effect=errors)

    with patch("time.sleep") as mock_sleep:
        rl.backoff_and_retry(mock_func, max_retries=3)

        assert mock_sleep.call_count == 2
        # First delay: 2^0 + jitter, second: 2^1 + jitter
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] < delays[1]  # Increasing backoff


def test_backoff_and_retry_max_retries_exhausted():
    """Test backoff_and_retry raises after max retries."""
    rl = RateLimiter()
    mock_func = MagicMock(side_effect=Exception("429 Too Many Requests"))

    with patch("time.sleep"):
        with pytest.raises(Exception, match="429"):
            rl.backoff_and_retry(mock_func, max_retries=2)

        assert mock_func.call_count == 2


def test_backoff_and_retry_non_rate_limit_error():
    """Test backoff_and_retry doesn't retry non-rate-limit errors."""
    rl = RateLimiter()
    mock_func = MagicMock(side_effect=ValueError("Invalid input"))

    with pytest.raises(ValueError, match="Invalid input"):
        rl.backoff_and_retry(mock_func)

    # Should not retry, only called once
    mock_func.assert_called_once()


def test_backoff_and_retry_custom_max_retries():
    """Test backoff_and_retry with custom max_retries."""
    rl = RateLimiter()
    mock_func = MagicMock(side_effect=Exception("429"))

    with patch("time.sleep"):
        with pytest.raises(Exception):
            rl.backoff_and_retry(mock_func, max_retries=5)

        assert mock_func.call_count == 5


# ==================== get_limit_info Tests ====================


def test_get_limit_info_exists():
    """Test get_limit_info returns stored info."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {"limit": 100, "remaining": 50, "reset": 1234567890}

    info = rl.get_limit_info("endpoint")

    assert info == {"limit": 100, "remaining": 50, "reset": 1234567890}


def test_get_limit_info_not_exists():
    """Test get_limit_info returns None for unknown endpoint."""
    rl = RateLimiter()

    info = rl.get_limit_info("unknown")

    assert info is None


# ==================== print_limits Tests ====================


def test_print_limits_no_data(capsys):
    """Test print_limits when no rate limit data available."""
    rl = RateLimiter()
    rl.print_limits()

    captured = capsys.readouterr()
    assert "No rate limit data available" in captured.out


def test_print_limits_with_data(capsys):
    """Test print_limits displays tracked endpoints."""
    rl = RateLimiter()
    rl.limits["endpoint1"] = {
        "limit": 100,
        "remaining": 80,
        "reset": int(time.time()) + 900,
    }
    rl.limits["endpoint2"] = {
        "limit": 50,
        "remaining": 3,
        "reset": int(time.time()) + 300,
    }

    rl.print_limits()

    captured = capsys.readouterr()
    assert "Rate Limit Status" in captured.out
    assert "endpoint1" in captured.out
    assert "endpoint2" in captured.out
    assert "[OK]" in captured.out  # endpoint1 at 80%
    assert "[ERROR]" in captured.out  # endpoint2 at 6%


def test_print_limits_warning_threshold(capsys):
    """Test print_limits shows [WARN] for mid-range remaining."""
    rl = RateLimiter()
    rl.limits["endpoint"] = {
        "limit": 100,
        "remaining": 30,  # 30% remaining
        "reset": int(time.time()) + 600,
    }

    rl.print_limits()

    captured = capsys.readouterr()
    assert "[WARN]" in captured.out


# ==================== Edge Cases ====================


def test_multiple_endpoints_tracked():
    """Test RateLimiter tracks multiple endpoints independently."""
    rl = RateLimiter()

    for i in range(5):
        headers = {
            "x-rate-limit-limit": str(100 + i),
            "x-rate-limit-remaining": str(50 + i),
            "x-rate-limit-reset": str(int(time.time()) + 600),
        }
        rl.update_from_headers(f"endpoint_{i}", headers)

    assert len(rl.limits) == 5
    assert rl.limits["endpoint_0"]["limit"] == 100
    assert rl.limits["endpoint_4"]["limit"] == 104


def test_backoff_base_configurable():
    """Test backoff_base affects retry delays."""
    rl = RateLimiter()
    rl.backoff_base = 3  # Change from default 2

    mock_func = MagicMock(side_effect=[Exception("429"), Exception("429"), "success"])

    with patch("time.sleep") as mock_sleep:
        rl.backoff_and_retry(mock_func)

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # With base 3: first ~3^0=1, second ~3^1=3
        assert delays[0] < 2  # ~1 + jitter
        assert delays[1] > 3  # ~3 + jitter
