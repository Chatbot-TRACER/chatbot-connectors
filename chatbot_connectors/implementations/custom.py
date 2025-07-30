"""Custom chatbot implementation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    JsonSerializable,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
)


class CustomResponseProcessor(ResponseProcessor):
    """Response processor for Custom chatbot."""

    def __init__(self, response_path: str) -> None:
        """Initialize the CustomResponseProcessor.

        Args:
            response_path: Dot-separated path to extract from the response JSON.

        Examples:
            - "message" -> response["message"]
            - "data.text" -> response["data"]["text"]
            - "messages.0.content" -> response["messages"][0]["content"]
            - "results.-1.value" -> response["results"][-1]["value"]
        """
        self.response_path = response_path

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Process the Custom response JSON and extract messages."""
        if not self.response_path:
            return ""

        try:
            value = response_json
            for key in self.response_path.split("."):
                if isinstance(value, list):
                    try:
                        index = int(key)
                        value = value[index]
                    except (ValueError, IndexError):
                        return ""  # Invalid key for list indexing
                else:
                    value = value[key]
            return str(value)
        except (KeyError, IndexError, TypeError, ValueError):
            return ""


@dataclass
class CustomEndpointConfig:
    """Configuration for a custom endpoint."""

    path: str
    method: RequestMethod = RequestMethod.POST
    headers: dict[str, str] = field(default_factory=dict)
    payload_template: dict[str, JsonSerializable] = field(default_factory=dict)


@dataclass
class CustomConfig(ChatbotConfig):
    """Configuration for Custom chatbot."""

    name: str = "Custom Chatbot"
    send_message: CustomEndpointConfig = field(default_factory=lambda: CustomEndpointConfig(path=""))
    response_path: str = ""

    @classmethod
    def from_yaml(cls, file_path: str) -> "CustomConfig":
        """Load configuration from a YAML file."""
        try:
            with Path(file_path).open() as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError as e:
            msg = f"Configuration file not found: {file_path}"
            raise FileNotFoundError(msg) from e
        except yaml.YAMLError as e:
            msg = f"Invalid YAML format in configuration file: {file_path}"
            raise yaml.YAMLError(msg) from e
        except Exception as e:
            msg = f"Error reading configuration file: {file_path}"
            raise OSError(msg) from e

        if not isinstance(config_data, dict):
            msg = f"Configuration file must contain a YAML dictionary: {file_path}"
            raise TypeError(msg)

        send_message_data = config_data.get("send_message", {})
        send_message_config = CustomEndpointConfig(
            path=send_message_data.get("path", "/"),
            method=RequestMethod(send_message_data.get("method", "POST").upper()),
            headers=send_message_data.get("headers", {}),
            payload_template=send_message_data.get("payload_template", {}),
        )

        return cls(
            name=config_data.get("name", "Custom Chatbot"),
            base_url=config_data.get("base_url", ""),
            timeout=config_data.get("timeout", 20),
            fallback_message=config_data.get("fallback_message", "I do not understand you"),
            headers=config_data.get("headers", {}),
            send_message=send_message_config,
            response_path=config_data.get("response_path", ""),
        )


class CustomChatbot(Chatbot):
    """Connector for a custom chatbot defined by a YAML file."""

    def __init__(self, config_path: str) -> None:
        """Initialize the Custom chatbot connector.

        Args:
            config_path: Path to the YAML configuration file.
        """
        self.custom_config = CustomConfig.from_yaml(config_path)
        super().__init__(self.custom_config)

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="config_path",
                type="string",
                required=True,
                description="The path to the YAML configuration file.",
            )
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for the custom chatbot."""
        return {
            "send_message": EndpointConfig(
                path=self.custom_config.send_message.path,
                method=self.custom_config.send_message.method,
                headers=self.custom_config.send_message.headers,
                timeout=self.custom_config.timeout,
            )
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for the custom chatbot."""
        return CustomResponseProcessor(response_path=self.custom_config.response_path)

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message to the custom chatbot.

        Args:
            user_msg: The user's message

        Returns:
            Payload dictionary for the API request
        """

        def replace_user_msg(obj: JsonSerializable) -> JsonSerializable:
            """Recursively replace {user_msg} placeholders in the payload template."""
            if isinstance(obj, dict):
                return {key: replace_user_msg(value) for key, value in obj.items()}
            if isinstance(obj, list):
                return [replace_user_msg(item) for item in obj]
            if isinstance(obj, str):
                return obj.replace("{user_msg}", user_msg)
            return obj

        return replace_user_msg(self.custom_config.send_message.payload_template)

    def _requires_conversation_id(self) -> bool:
        """Custom chatbot conversation tracking depends on the implementation."""
        return False
