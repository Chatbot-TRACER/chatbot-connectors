"""Connector for the Codex and Claude Code CLI agent gateway."""

from dataclasses import dataclass
from typing import Any

import requests

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
)
from chatbot_connectors.exceptions import ConnectorConnectionError


class CliAgentGatewayResponseProcessor(ResponseProcessor):
    """Extract assistant text from the gateway response envelope."""

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Return the content of the assistant message."""
        if not isinstance(response_json, dict):
            return ""

        message = response_json.get("message")
        if not isinstance(message, dict):
            return ""

        content = message.get("content")
        return content if isinstance(content, str) else ""


@dataclass
class CliAgentGatewayConfig(ChatbotConfig):
    """Configuration shared by the Codex and Claude Code gateways."""


class CliAgentGatewayChatbot(Chatbot):
    """Stateful connector for a cli-agent-gateway HTTP service."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float | tuple[float, float] | None = 660,
    ) -> None:
        """Initialize the gateway connector.

        Args:
            base_url: Gateway URL. By default Codex uses port 3000 and Claude
                Code uses port 3001.
            api_key: Optional value configured as SERVICE_API_KEY by the gateway.
            timeout: Request timeout in seconds or a (connect, read) tuple.
        """
        normalized_base_url = f"{base_url.rstrip('/')}/"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        config = CliAgentGatewayConfig(
            base_url=normalized_base_url,
            timeout=timeout,
            headers=headers,
        )
        super().__init__(config)

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return parameters accepted by the CLI agent gateway connector."""
        return [
            Parameter(
                name="base_url",
                type="string",
                required=True,
                description="CLI agent gateway URL (Codex defaults to port 3000; Claude Code to 3001).",
            ),
            Parameter(
                name="api_key",
                type="string",
                required=False,
                description="Optional gateway SERVICE_API_KEY value.",
            ),
            Parameter(
                name="timeout",
                type="integer",
                required=False,
                description="Maximum time to wait for the CLI agent to finish a message.",
                default=660,
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return gateway endpoint configurations for the active conversation."""
        return {
            "health_check": EndpointConfig(
                path="health",
                method=RequestMethod.GET,
                timeout=self.config.timeout,
            ),
            "new_conversation": EndpointConfig(
                path="conversations",
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
            "send_message": EndpointConfig(
                path=f"conversations/{self.conversation_id}/messages",
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the gateway response processor."""
        return CliAgentGatewayResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Build the gateway message request."""
        return {"message": user_msg}

    def create_new_conversation(self) -> bool:
        """Create and retain a fresh gateway conversation identifier."""
        self.conversation_id = None
        endpoint = self.get_endpoints()["new_conversation"]
        url = self.config.get_full_url(endpoint.path)

        try:
            response = self._make_request(url, endpoint, {})
        except requests.RequestException as exc:
            message = f"Failed to create a CLI agent gateway conversation at {url}"
            raise ConnectorConnectionError(message, original_error=exc) from exc

        if not isinstance(response, dict):
            return False
        conversation_id = response.get("id")
        if not isinstance(conversation_id, str) or not conversation_id:
            return False

        self.conversation_id = conversation_id
        return True
