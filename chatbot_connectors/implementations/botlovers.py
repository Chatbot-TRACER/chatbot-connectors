"""Legacy Botlovers module removed.

This module is kept to provide a clear error message for projects that still
import ``chatbot_connectors.implementations.botlovers``. Please migrate to
``chatbot_connectors.implementations.botslovers``.
"""

from __future__ import annotations

msg = (
    "The 'chatbot_connectors.implementations.botlovers' module has been removed. "
    "Please import 'chatbot_connectors.implementations.botslovers' instead."
)


def __getattr__(name: str) -> None:  # pragma: no cover - defensive guard
    """Always raise to signal that the legacy module is gone."""
    raise ImportError(msg)


def __dir__() -> list[str]:  # pragma: no cover - defensive guard
    """Return an empty list as the module exposes no symbols."""
    return []
