"""Tests for scheduler time window selection including extended windows."""

from datetime import time as dtime

from scheduler import current_slot


def test_current_slot_standard_windows():
    windows = ["morning", "afternoon", "evening"]
    assert current_slot(windows, now=dtime(9, 30)) == "morning"
    assert current_slot(windows, now=dtime(15, 0)) == "afternoon"
    assert current_slot(windows, now=dtime(19, 30)) == "evening"


def test_current_slot_extended_windows():
    windows = ["early-morning", "morning", "night", "late-night"]
    # Early morning
    assert current_slot(windows, now=dtime(5, 30)) == "early-morning"
    # Morning
    assert current_slot(windows, now=dtime(10, 0)) == "morning"
    # Night
    assert current_slot(windows, now=dtime(21, 30)) == "night"
    # Late-night across midnight (after 23:00)
    assert current_slot(windows, now=dtime(23, 30)) == "late-night"
    # Late-night before 02:00
    assert current_slot(windows, now=dtime(1, 30)) == "late-night"


def test_current_slot_fallback_random():
    windows = ["morning"]
    # Outside morning -> returns one of windows (only morning) so deterministic
    assert current_slot(windows, now=dtime(8, 0)) == "morning"


def test_current_slot_empty_list():
    assert current_slot([], now=dtime(12, 0)) is None
