"""Template-based content generation and interaction actions."""

from __future__ import annotations

from business.content import REPLY_TEMPLATES, TEMPLATES, choose_template, helpful_reply, make_post
from orchestration.engine import act_on_search as _engine_act_on_search



# Re-export from business layer for backward compatibility
__all__ = [
    "TEMPLATES",
    "REPLY_TEMPLATES",
    "choose_template",
    "make_post",
    "helpful_reply",
    "act_on_search",
]


def act_on_search(*args, **kwargs):  # type: ignore[override]
    """Backward-compatible shim delegating to orchestration.engine.act_on_search.

    NOTE: This will be deprecated in Phase 4. Import from `orchestration.engine` instead.
    """
    return _engine_act_on_search(*args, **kwargs)
