"""Metro Madrid chatbot implementation."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from collections.abc import Callable

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
from chatbot_connectors.logging_utils import get_logger

logger = get_logger()


class MetroMadridResponseProcessor(ResponseProcessor):
    """Response processor for Metro Madrid chatbot responses."""

    def __init__(self, button_callback: Callable[[dict[str, str]], None] | None = None) -> None:
        """Initialize the processor with an optional callback for button updates."""
        self._button_callback = button_callback

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract textual replies and summarize available buttons."""
        messages = self._extract_messages(response_json)
        if not messages:
            self._notify_buttons({})
            return ""

        collected_messages: list[str] = []
        button_map: dict[str, str] = {}

        for item in messages:
            if self._is_user_echo(item):
                continue

            text = self._extract_message_text(item)
            if text:
                collected_messages.append(text)

            buttons_text, extracted_buttons = self._extract_buttons(item)
            if buttons_text:
                collected_messages.append(buttons_text)
            button_map.update(extracted_buttons)

        self._notify_buttons(button_map)
        return self._format_collected_messages(collected_messages)

    def _extract_messages(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return a sanitized list of message dictionaries."""
        if not isinstance(response_json, dict):
            return []

        messages = response_json.get("messages")
        if not isinstance(messages, list):
            return []

        return [item for item in messages if isinstance(item, dict)]

    def _notify_buttons(self, buttons: dict[str, str]) -> None:
        """Send button metadata to the registered callback, if any."""
        if self._button_callback:
            self._button_callback(buttons)

    @staticmethod
    def _format_collected_messages(collected_messages: list[str]) -> str:
        """Join message snippets with spacing suitable for final output."""
        return "\n\n".join(collected_messages).strip()

    @staticmethod
    def _is_user_echo(message: dict[str, Any]) -> bool:
        """Return True when the message corresponds to user echoes."""
        message_type = message.get("type")
        return isinstance(message_type, str) and message_type.lower() == "user"

    @staticmethod
    def _extract_message_text(message: dict[str, Any]) -> str | None:
        """Return normalized textual content from a message entry."""
        content = message.get("content")
        if not isinstance(content, str):
            return None

        stripped_content = content.strip()
        return stripped_content or None

    def _extract_buttons(self, message: dict[str, Any]) -> tuple[str | None, dict[str, str]]:
        """Gather button metadata and renderable lines for quick replies."""
        buttons = message.get("buttons")
        if not isinstance(buttons, list):
            return None, {}

        button_lines: list[str] = []
        button_map: dict[str, str] = {}
        for button in buttons:
            if not isinstance(button, dict):
                continue

            label = button.get("content") or button.get("text") or button.get("value")
            button_id = button.get("idButton") or button.get("value")
            if not isinstance(button_id, str):
                continue

            if isinstance(label, str):
                button_map[button_id] = label
                button_lines.append(f"[{button_id}] {label}")
            else:
                button_map.setdefault(button_id, "")
                button_lines.append(f"[{button_id}]")

        if not button_lines:
            return None, button_map

        formatted = "Buttons:\n" + "\n".join(button_lines)
        return formatted, button_map


@dataclass
class MetroMadridConfig(ChatbotConfig):
    """Configuration specific to the Metro Madrid chatbot."""

    id_project: str = "Mzpv0w4t71t"
    id_client: str = "0"
    origin: str = "https://www.metromadrid.es"
    referer: str = "https://www.metromadrid.es/"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"
    accept_language: str = "es-ES,es;q=0.9,en;q=0.8"
    conversation_path: str = "/WidgetConversation"
    message_path: str = "/WidgetMessage"
    user_generate_path: str = "/WidgetUserGenerate"
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure base URL normalization and merge headers."""
        if not self.base_url.endswith("/"):
            self.base_url = f"{self.base_url}/"

        default_headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.origin,
            "Referer": self.referer,
            "User-Agent": self.user_agent,
        }
        if self.accept_language:
            default_headers["Accept-Language"] = self.accept_language

        merged_headers = {**default_headers, **self.headers}
        self.headers = merged_headers


class MetroMadridChatbot(Chatbot):
    """Connector for Metro Madrid chatbot API."""

    DEFAULT_BASE_URL = "https://kdcaapi.metromadrid.es/api/KDCA/"
    ONBOARDING_ERROR_MESSAGE = "Failed to complete Metro Madrid onboarding"

    def __init__(self, language: str = "es") -> None:
        """Initialize the Metro Madrid chatbot connector."""
        config = MetroMadridConfig(
            base_url=self.DEFAULT_BASE_URL,
        )
        super().__init__(config)
        self.metro_config = config
        self.user_info: dict[str, str] | None = None
        self._button_lookup: dict[str, str] = {}
        self._button_id_to_label: dict[str, str] = {}
        self._response_processor = MetroMadridResponseProcessor(self._update_button_cache)
        self._language = self._normalize_language(language)

        if not self.create_new_conversation():
            msg = "Failed to initialize Metro Madrid chatbot session"
            raise ConnectorConnectionError(msg)

        try:
            self.complete_onboarding(self._language)
        except ConnectorConnectionError:
            raise
        except Exception as err:
            logger.exception("Metro Madrid handshake failed")
            raise ConnectorConnectionError(self.ONBOARDING_ERROR_MESSAGE) from err

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="language",
                type="string",
                required=False,
                description="Handshake language (es or en).",
                default="es",
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for Metro Madrid chatbot."""
        return {
            "generate_user": EndpointConfig(
                path=self.metro_config.user_generate_path,
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
            "conversation": EndpointConfig(
                path=self.metro_config.conversation_path,
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
            "send_message": EndpointConfig(
                path=self.metro_config.message_path,
                method=RequestMethod.POST,
                timeout=self.config.timeout,
            ),
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for Metro Madrid chatbot."""
        return self._response_processor

    def create_new_conversation(self) -> bool:
        """Create a new session with Metro Madrid API."""
        endpoints = self.get_endpoints()
        endpoint_config = endpoints["generate_user"]
        url = self.config.get_full_url(endpoint_config.path)
        payload = {
            "idProject": self.metro_config.id_project,
            "idClient": self.metro_config.id_client,
        }

        try:
            response = self._make_request(url, endpoint_config, payload)
        except requests.RequestException:
            logger.exception("Failed to create Metro Madrid session at %s", url)
            return False

        if not isinstance(response, dict):
            return False

        nickname = response.get("nickname")
        session = response.get("session")
        if not isinstance(nickname, str) or not isinstance(session, str):
            return False

        self.user_info = {"nickname": nickname, "session": session}
        self.conversation_id = session
        self._clear_button_cache()
        return True

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare payload for sending messages."""
        if not self.user_info:
            msg = "Metro Madrid session not initialized"
            raise ConnectorConnectionError(msg)

        content, button_id = self._parse_user_input(user_msg)

        return {
            "idProject": self.metro_config.id_project,
            "idClient": self.metro_config.id_client,
            "data": {
                "type": "text",
                "content": content,
                "buttonId": button_id,
                "user": self.user_info,
            },
        }

    def fetch_conversation_messages(self) -> dict[str, Any] | None:
        """Retrieve the latest conversation transcript from the API."""
        if not self.user_info:
            return None

        endpoints = self.get_endpoints()
        endpoint_config = endpoints["conversation"]
        url = self.config.get_full_url(endpoint_config.path)
        payload = {
            "idProject": self.metro_config.id_project,
            "idClient": self.metro_config.id_client,
            "data": {"user": self.user_info},
        }

        try:
            response = self._make_request(url, endpoint_config, payload)
        except requests.RequestException:
            logger.exception("Failed to retrieve Metro Madrid conversation at %s", url)
            return None

        if isinstance(response, dict):
            # Update button cache to keep quick replies in sync
            self._update_button_cache_from_response(response)
        return response

    def complete_onboarding(self, language: str | None = None) -> None:
        """Complete the required onboarding flow (language + privacy)."""
        if not self.user_info:
            msg = "Metro Madrid session not initialized"
            raise ConnectorConnectionError(msg)

        chosen_language = language or self._language
        normalized_lang = self._normalize_language(chosen_language)
        language_button_id, initial_prompt = self._get_handshake_values(normalized_lang)

        steps = [initial_prompt, f"button:{language_button_id}", "button:PGDPRSI"]

        for step in steps:
            success, _reply = self.execute_with_input(step)
            if not success:
                msg = f"Onboarding step failed while sending '{step}'"
                raise ConnectorConnectionError(msg)

        self._language = normalized_lang

    def _parse_user_input(self, user_msg: str) -> tuple[str, str | None]:
        """Determine whether the user wants to click a button or send plain text."""
        trimmed = user_msg.strip()
        if not trimmed:
            return "", None

        explicit_button_id, explicit_content = self._extract_explicit_button(trimmed)
        if explicit_button_id:
            content = explicit_content or self._button_id_to_label.get(explicit_button_id, "")
            if not content:
                content = trimmed
            return content, explicit_button_id

        normalized = self._normalize_button_key(trimmed)
        cached_id = self._button_lookup.get(normalized)
        if cached_id:
            content = self._button_id_to_label.get(cached_id, trimmed)
            return content, cached_id

        return trimmed, None

    def _get_handshake_values(self, language: str) -> tuple[str, str]:
        """Return button identifier and seed message for the desired language."""
        if language == "es":
            return "SPNSHYES", "Hola"
        if language == "en":
            return "NGLSHYES", "Hello"

        msg = f"Unsupported onboarding language '{language}'"
        raise ConnectorConnectionError(msg)

    def _normalize_language(self, language: str) -> str:
        """Normalize a language selector to a supported code."""
        if not language:
            msg = "Language selection cannot be empty"
            raise ConnectorConnectionError(msg)

        normalized = unicodedata.normalize("NFKD", language).encode("ascii", "ignore").decode("ascii")
        normalized = normalized.strip().casefold()

        if normalized in {"es", "espanol", "spanish", "es-419"}:
            return "es"
        if normalized in {"en", "english", "eng"}:
            return "en"

        msg = f"Unsupported onboarding language '{language}'"
        raise ConnectorConnectionError(msg)

    def _extract_explicit_button(self, message: str) -> tuple[str | None, str | None]:
        """Extract button identifier directives from the user message."""
        lowered = message.lower()
        prefixes = ("button:", "button_id:", "button=", "button_id=")
        for prefix in prefixes:
            if lowered.startswith(prefix):
                remainder = message[len(prefix) :].strip()
                if not remainder:
                    return None, None

                separators = ("::", "|", ";", ",")
                for separator in separators:
                    if separator in remainder:
                        button_id, content = remainder.split(separator, 1)
                        return button_id.strip() or None, content.strip() or None

                if " " in remainder:
                    button_id, content = remainder.split(" ", 1)
                    return button_id.strip() or None, content.strip() or None

                return remainder.strip() or None, None
        return None, None

    def _update_button_cache(self, buttons: dict[str, str]) -> None:
        """Update quick reply cache using button metadata."""
        self._clear_button_cache()
        if not buttons:
            return

        for button_id, label in buttons.items():
            if not isinstance(button_id, str):
                continue

            normalized_id = self._normalize_button_key(button_id)
            self._button_lookup[normalized_id] = button_id

            if isinstance(label, str) and label:
                self._button_id_to_label[button_id] = label
                normalized_label = self._normalize_button_key(label)
                self._button_lookup[normalized_label] = button_id

    def _update_button_cache_from_response(self, response: dict[str, Any]) -> None:
        """Extract buttons from the response and refresh the cache."""
        messages = response.get("messages")
        if not isinstance(messages, list):
            self._clear_button_cache()
            return

        extracted: dict[str, str] = {}
        for item in messages:
            if not isinstance(item, dict):
                continue

            buttons = item.get("buttons")
            if not isinstance(buttons, list):
                continue

            for button in buttons:
                if not isinstance(button, dict):
                    continue

                button_id = button.get("idButton") or button.get("value")
                label = button.get("content") or button.get("text") or button.get("value")
                if isinstance(button_id, str):
                    extracted[button_id] = label if isinstance(label, str) else ""

        self._update_button_cache(extracted)

    def _clear_button_cache(self) -> None:
        """Reset cached quick replies."""
        self._button_lookup.clear()
        self._button_id_to_label.clear()

    @staticmethod
    def _normalize_button_key(value: str) -> str:
        """Normalize values to make button lookups forgiving."""
        return " ".join(value.casefold().split())
