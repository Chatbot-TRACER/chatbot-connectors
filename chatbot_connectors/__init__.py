"""Chatbot Connectors Library.

A library for connecting to various chatbot APIs.
"""

# Import registry to auto-register chatbots
from chatbot_connectors import registry
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

__version__ = "0.1.0"

__all__ = [
    "Chatbot",
    "ChatbotConfig",
    "ChatbotFactory",
    "ChatbotResponse",
    "ConnectorAuthenticationError",
    "ConnectorConfigurationError",
    "ConnectorConnectionError",
    "ConnectorError",
    "ConnectorResponseError",
    "EndpointConfig",
    "Parameter",
    "RequestMethod",
    "ResponseProcessor",
    "SimpleTextProcessor",
    "registry",
]
