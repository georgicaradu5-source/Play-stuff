"""Orchestration layer for actions and scheduling glue.

Exports orchestrator functions to keep callers stable during migration.
"""
from .engine import act_on_search  # re-export for convenience

__all__ = ["act_on_search"]
