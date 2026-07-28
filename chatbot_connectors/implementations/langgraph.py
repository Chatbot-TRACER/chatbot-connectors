"""LangGraph Agent Server chatbot implementation."""

from dataclasses import dataclass
from typing import Any, ClassVar

import requests

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
    extract_json_path,
)
from chatbot_connectors.exceptions import ConnectorConnectionError


class LangGraphResponseProcessor(ResponseProcessor):
    """Extract the last assistant message from a LangGraph run result."""

    _ASSISTANT_ROLES: ClassVar[frozenset[str]] = frozenset({"ai", "assistant"})

    def __init__(self, response_path: str = "messages") -> None:
        """Initialize the processor with the graph-state response path."""
        self.response_path = response_path

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract response text from the final state returned by runs/wait."""
        value: Any = response_json
        if self.response_path:
            value = extract_json_path(response_json, self.response_path)

        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return self._content_to_text(value.get("content"))
        if not isinstance(value, list):
            return ""

        for message in reversed(value):
            if not isinstance(message, dict):
                continue
            role = message.get("role") or message.get("type")
            if role in self._ASSISTANT_ROLES:
                return self._content_to_text(message.get("content"))

        return ""

    @classmethod
    def _content_to_text(cls, content: object) -> str:
        """Normalize string and content-block message formats to plain text."""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            text = content.get("text")
            return text if isinstance(text, str) else ""
        if not isinstance(content, list):
            return ""

        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return "".join(text_parts)


@dataclass
class LangGraphConfig(ChatbotConfig):
    """Configuration for a LangGraph Agent Server deployment."""

    assistant_id: str = "chatbot"
    response_path: str = "messages"


class LangGraphChatbot(Chatbot):
    """Connector for stateful graphs exposed through LangGraph Agent Server."""

    def __init__(
        self,
        base_url: str,
        assistant_id: str = "chatbot",
        api_key: str | None = None,
        response_path: str = "messages",
        timeout: float | tuple[float, float] | None = 120,
    ) -> None:
        """Initialize a LangGraph Agent Server connector.

        Args:
            base_url: Agent Server URL, for example http://127.0.0.1:8101.
            assistant_id: Graph/assistant identifier configured in langgraph.json.
            api_key: Optional LangSmith deployment API key.
            response_path: Dot-separated path to the response in the final graph state.
            timeout: Request timeout in seconds or a (connect, read) tuple.
        """
        normalized_base_url = f"{base_url.rstrip('/')}/"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Api-Key"] = api_key

        config = LangGraphConfig(
            base_url=normalized_base_url,
            assistant_id=assistant_id,
            response_path=response_path,
            timeout=timeout,
            headers=headers,
        )
        super().__init__(config)
        self.langgraph_config = config

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return parameters accepted by the LangGraph connector."""
        return [
            Parameter(
                name="base_url",
                type="string",
                required=True,
                description="LangGraph Agent Server base URL.",
            ),
            Parameter(
                name="assistant_id",
                type="string",
                required=False,
                description="Graph ID from langgraph.json.",
                default="chatbot",
            ),
            Parameter(
                name="api_key",
                type="string",
                required=False,
                description="Optional API key for a remote LangSmith deployment.",
            ),
            Parameter(
                name="response_path",
                type="string",
                required=False,
                description="Dot-separated response path in the final graph state.",
                default="messages",
            ),
            Parameter(
                name="timeout",
                type="integer",
                required=False,
                description="Maximum time to wait for a synchronous graph run.",
                default=120,
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return Agent Server endpoint configurations."""
        return {
            "health_check": EndpointConfig(path="ok", method=RequestMethod.GET, timeout=self.config.timeout),
            "new_conversation": EndpointConfig(path="threads", method=RequestMethod.POST, timeout=self.config.timeout),
            "send_message": EndpointConfig(
                path=f"threads/{self.conversation_id}/runs/wait",
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the processor for the final LangGraph state."""
        return LangGraphResponseProcessor(self.langgraph_config.response_path)

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Build a stateful synchronous run request."""
        return {
            "assistant_id": self.langgraph_config.assistant_id,
            "input": {"messages": [{"role": "user", "content": user_msg}]},
        }

    def create_new_conversation(self) -> bool:
        """Create a fresh Agent Server thread and store its identifier."""
        self.conversation_id = None
        endpoint = self.get_endpoints()["new_conversation"]
        url = self.config.get_full_url(endpoint.path)

        try:
            response = self._make_request(url, endpoint, {})
        except requests.RequestException as exc:
            message = f"Failed to create a LangGraph thread at {url}"
            raise ConnectorConnectionError(message, original_error=exc) from exc

        if not isinstance(response, dict):
            return False
        thread_id = response.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            return False

        self.conversation_id = thread_id
        return True
