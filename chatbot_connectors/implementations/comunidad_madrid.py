"""Comunidad de Madrid chatbot implementation."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
)


class ComunidadMadridResponseProcessor(ResponseProcessor):
    """Response processor for Comunidad de Madrid chatbot responses."""

    TEXT_KEYS = (
        "text",
        "message",
        "content",
        "answer",
        "response",
        "reply",
        "description",
        "written_text",
    )

    BUTTON_KEYS = ("buttons", "options", "quick_replies", "suggestions")

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract textual replies and available buttons from the response."""
        text_parts: list[str] = []
        self._collect_text(response_json, text_parts)
        return "\n\n".join(dict.fromkeys(part.strip() for part in text_parts if part.strip()))

    def _collect_text(self, value: object, text_parts: list[str]) -> None:
        """Recursively collect text from common chatbot response shapes."""
        if isinstance(value, list):
            for item in value:
                self._collect_text(item, text_parts)
            return

        if not isinstance(value, dict):
            return

        self._collect_direct_text(value, text_parts)
        self._collect_buttons(value, text_parts)

        for item in value.values():
            if isinstance(item, (dict, list)):
                self._collect_text(item, text_parts)

    def _collect_direct_text(self, value: dict[str, Any], text_parts: list[str]) -> None:
        """Collect direct text fields from one response object."""
        for key in self.TEXT_KEYS:
            item = value.get(key)
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, (dict, list)):
                self._collect_text(item, text_parts)

    def _collect_buttons(self, value: dict[str, Any], text_parts: list[str]) -> None:
        """Collect readable quick replies from one response object."""
        for button_key in self.BUTTON_KEYS:
            button_lines = self._format_buttons(value.get(button_key))
            if button_lines:
                text_parts.append("Buttons:\n" + "\n".join(button_lines))

    @staticmethod
    def _format_buttons(buttons: object) -> list[str]:
        """Return readable button lines from common button payload shapes."""
        if not isinstance(buttons, list):
            return []

        button_lines: list[str] = []
        for button in buttons:
            if isinstance(button, str):
                button_lines.append(f"- {button}")
                continue

            if not isinstance(button, dict):
                continue

            label = button.get("text") or button.get("title") or button.get("label") or button.get("content")
            value = button.get("value") or button.get("payload") or button.get("id") or button.get("url")
            if isinstance(label, str) and isinstance(value, str) and label != value:
                button_lines.append(f"- {label}: {value}")
            elif isinstance(label, str):
                button_lines.append(f"- {label}")
            elif isinstance(value, str):
                button_lines.append(f"- {value}")

        return button_lines


@dataclass
class ComunidadMadridConfig(ChatbotConfig):
    """Configuration specific to the Comunidad de Madrid chatbot."""

    consumer_client: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJjb25zdW1lcl9jbGllbnQiOiJhdmF0YXIiLCJjcmVhdGlvbl90aW1lIjoiMjAyNi0wNC0yMyAxMjowNTowMCJ9."
        "wEEIoTdPHi35l2lxiQYJOpLp_E5sC-tZcmZwDQmJRwA"
    )
    origin: str = "https://www.comunidad.madrid"
    referer: str = "https://www.comunidad.madrid/"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    )
    accept_language: str = "es-ES,es;q=0.9,en;q=0.8"
    message_path: str = "/api-avatar/new-message"
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Merge browser-like headers required by the public widget API."""
        default_headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self.origin,
            "Referer": self.referer,
            "User-Agent": self.user_agent,
        }
        if self.accept_language:
            default_headers["Accept-Language"] = self.accept_language

        self.headers = {**default_headers, **self.headers}


class ComunidadMadridChatbot(Chatbot):
    """Connector for Comunidad de Madrid's public avatar chatbot API."""

    DEFAULT_BASE_URL = "https://avatar.comunidad.madrid"

    def __init__(
        self,
        *,
        conversation_id: str = "",
        consumer_client: str | None = None,
        timeout: float | tuple[float, float] | None = 60,
    ) -> None:
        """Initialize the Comunidad de Madrid chatbot connector."""
        config = ComunidadMadridConfig(base_url=self.DEFAULT_BASE_URL, timeout=timeout)
        if consumer_client:
            config.consumer_client = consumer_client

        super().__init__(config)
        self.comunidad_config = config
        self.conversation_id = conversation_id or self._generate_conversation_id()

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="conversation_id",
                type="string",
                required=False,
                description="Optional conversation_id captured from the widget. Defaults to a generated 24-char hex id.",
                default="",
            ),
            Parameter(
                name="consumer_client",
                type="string",
                required=False,
                description="Public consumer_client JWT used by the Comunidad de Madrid avatar widget.",
                default=ComunidadMadridConfig.consumer_client,
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for Comunidad de Madrid chatbot."""
        return {
            "send_message": EndpointConfig(
                path=self.comunidad_config.message_path,
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            )
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for Comunidad de Madrid chatbot."""
        return ComunidadMadridResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare payload for sending messages."""
        return {
            "conversation_id": self.conversation_id,
            "written_text": user_msg,
            "consumer_client": self.comunidad_config.consumer_client,
        }

    def create_new_conversation(self) -> bool:
        """Create a local conversation identifier matching the widget format."""
        self.conversation_id = self._generate_conversation_id()
        return True

    @staticmethod
    def _generate_conversation_id() -> str:
        """Return a 24-character hexadecimal conversation id."""
        return secrets.token_hex(12)
