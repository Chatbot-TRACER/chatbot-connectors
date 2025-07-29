"""Chatbot Connectors Library.

A library for connecting to various chatbot APIs.
"""

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    ChatbotResponse,
    EndpointConfig,
    Parameter,
    RequestMethod,
    ResponseProcessor,
    SimpleTextProcessor,
)
from chatbot_connectors.exceptions import (
    ConnectorAuthenticationError,
    ConnectorConfigurationError,
    ConnectorConnectionError,
    ConnectorError,
    ConnectorResponseError,
)
from chatbot_connectors.factory import ChatbotFactory

# Import registry to auto-register chatbots
from chatbot_connectors import registry  # noqa: F401

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "Chatbot",
    "ChatbotConfig", 
    "ChatbotResponse",
    "EndpointConfig",
    "Parameter",
    "RequestMethod",
    "ResponseProcessor",
    "SimpleTextProcessor",
    # Exceptions
    "ConnectorError",
    "ConnectorConnectionError",
    "ConnectorAuthenticationError",
    "ConnectorConfigurationError",
    "ConnectorResponseError",
    # Factory
    "ChatbotFactory",
]
