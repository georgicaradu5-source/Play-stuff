"""Orchestration layer for actions and scheduling glue.

Exports orchestrator functions to keep callers stable during migration.
"""
from .engine import (
    act_on_search,
    current_slot,
    run_interact_actions,
    run_post_action,
    run_scheduler,
)

__all__ = [
    "act_on_search",
    "current_slot",
    "run_interact_actions",
    "run_post_action",
    "run_scheduler",
]
