"""Simple logging utilities for chatbot connectors."""

import logging


def get_logger(name: str = "chatbot_connectors") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name, defaults to "chatbot_connectors"

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
