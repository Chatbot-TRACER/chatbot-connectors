"""Botlovers chatbot implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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
from chatbot_connectors.logging_utils import get_logger

logger = get_logger()


class BotloversResponseProcessor(ResponseProcessor):
    """Response processor for Botlovers chatbot."""

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Extract textual replies from Botlovers responses."""
        if not isinstance(response_json, dict):
            return ""

        text_parts = self._collect_message_texts(response_json)
        if text_parts:
            return "\n".join(text_parts)

        return self._extract_fallback_text(response_json)

    def _collect_message_texts(self, response_json: dict[str, Any]) -> list[str]:
        """Collect textual responses from nested message groups."""
        messages = response_json.get("messages")
        collected: list[str] = []

        if not isinstance(messages, list):
            return collected

        for group in messages:
            if isinstance(group, dict):
                self._append_message_content(group, collected)
                continue

            if not isinstance(group, list):
                continue

            for item in group:
                if not isinstance(item, dict):
                    continue
                self._append_message_content(item, collected)

        return collected

    def _append_message_content(self, item: dict[str, Any], collector: list[str]) -> None:
        """Append message text and quick replies to the collector."""
        text = self._extract_text_from_message(item)
        if text:
            collector.append(text)

        quick_replies = self._extract_quick_replies(item)
        if quick_replies:
            collector.append(quick_replies)

    def _extract_fallback_text(self, response_json: dict[str, Any]) -> str:
        """Extract fallback answer from response_gpt if available."""
        data = response_json.get("data")
        if not isinstance(data, dict):
            return ""

        gpt_response = data.get("response_gpt")
        if not isinstance(gpt_response, dict):
            return ""

        answer = gpt_response.get("answer")
        if isinstance(answer, str):
            return answer

        return ""

    def _extract_quick_replies(self, item: dict[str, Any]) -> str:
        """Extract quick replies from the message if present."""
        message = item.get("message")
        if not isinstance(message, dict):
            return ""

        quick_replies = message.get("quick_replies")
        if not isinstance(quick_replies, list):
            return ""

        titles: list[str] = []
        for reply in quick_replies:
            if not isinstance(reply, dict):
                continue
            title = reply.get("title") or reply.get("payload")
            if isinstance(title, str):
                titles.append(title)

        if not titles:
            return ""

        return f"Options: {', '.join(titles)}"

    def _extract_text_from_message(self, item: dict[str, Any]) -> str:
        """Extract the text field handling the nested payload format."""
        message = item.get("message")
        if isinstance(message, dict):
            text = message.get("text")
            if isinstance(text, str):
                return text

            nested_message = message.get("message")
            if isinstance(nested_message, dict):
                nested_text = nested_message.get("text")
                if isinstance(nested_text, str):
                    return nested_text

        return ""


@dataclass
class BotloversConfig(ChatbotConfig):
    """Configuration specific to Botlovers chatbot."""

    lang: str = "es"
    channel: str = "web"
    widget_form: str = "TRUE"
    accept_terminos: int = 1
    contexto_extra: list[Any] = field(default_factory=list)
    session_refresh_seconds: int = 300

    def __post_init__(self) -> None:
        """Normalize configuration inputs."""
        if not self.base_url.endswith("/"):
            self.base_url = f"{self.base_url}/"

        default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        merged_headers = {**default_headers, **self.headers}
        self.headers = merged_headers


class BotloversChatbot(Chatbot):
    """Connector for the Botlovers chatbot API."""

    def __init__(
        self,
        base_url: str,
        lang: str = "es",
        timeout: int = 20,
        session_refresh_seconds: int = 300,
    ) -> None:
        """Initialize the Botlovers chatbot connector."""
        config = BotloversConfig(
            base_url=base_url,
            lang=lang,
            timeout=timeout,
            session_refresh_seconds=session_refresh_seconds,
        )
        super().__init__(config)

        self.botlovers_config = config
        self.id_user: str | None = None
        self.idweb_user: str | None = None
        self.session_token: str | None = None
        self.latest_response: dict[str, Any] | None = None
        self.session_last_updated: datetime | None = None
        self._initialize_conversation()

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="base_url",
                type="string",
                required=True,
                description="The base URL for the Botlovers deployment, e.g. https://alcampo.botslovers.com/",
            ),
            Parameter(
                name="lang",
                type="string",
                required=False,
                description="Language code used for the conversation.",
                default="es",
            ),
            Parameter(
                name="session_refresh_seconds",
                type="integer",
                required=False,
                description="Seconds before forcing a session refresh via check_session.",
                default=300,
            ),
        ]

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for Botlovers chatbot."""

        def _endpoint() -> EndpointConfig:
            return EndpointConfig(path="/bot/web", method=RequestMethod.POST, timeout=self.config.timeout)

        return {
            "user_check": _endpoint(),
            "check_session": _endpoint(),
            "send_message": _endpoint(),
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for Botlovers chatbot."""
        return BotloversResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message to Botlovers."""
        if not all([self.id_user, self.idweb_user, self.session_token]):
            error_msg = "Botlovers session not initialized"
            raise ValueError(error_msg)

        message_payload = {
            "message": {"message": {"text": user_msg}},
            "iduser": self.id_user,
            "session": self.session_token,
            "channel": self.botlovers_config.channel,
        }

        data_section = {
            "id_user": self.id_user,
            "idweb_user": self.idweb_user,
            "session": self.session_token,
            "message": message_payload,
            "widget_form": self.botlovers_config.widget_form,
            "contexto_extra": list(self.botlovers_config.contexto_extra),
            "lang": self.botlovers_config.lang,
        }

        return {"data": data_section, "accion": "response_bot"}

    def execute_with_input(self, user_msg: str) -> tuple[bool, str | None]:
        """Send a message to the chatbot and update session state."""
        endpoints = self.get_endpoints()
        endpoint_config = endpoints.get("send_message")
        if not endpoint_config:
            return False, "Send message endpoint not configured"

        last_exception: requests.RequestException | None = None
        url = self.config.get_full_url(endpoint_config.path)

        for attempt in range(3):
            if self.conversation_id is None and self._requires_conversation_id() and not self.create_new_conversation():
                return False, "Failed to initialize conversation"

            self._refresh_session_if_needed()

            try:
                payload = self.prepare_message_payload(user_msg)
            except ValueError:
                self._invalidate_session()
                continue

            try:
                response_json = self._make_request(url, endpoint_config, payload)
            except requests.RequestException as exc:
                last_exception = exc
                logger.warning("Botlovers request attempt %s failed: %s", attempt + 1, exc)
                self._invalidate_session()
                continue

            if response_json:
                if isinstance(response_json, dict):
                    self._update_session_state(response_json)
                processor = self.get_response_processor()
                response_input = response_json if isinstance(response_json, (dict, list)) else {}
                response_text = processor.process(response_input) if response_input else ""
                return True, response_text
            logger.warning("Botlovers request attempt %s returned empty response", attempt + 1)
            self._invalidate_session()
            continue

        if last_exception is not None:
            logger.exception("Chatbot request failed for Botlovers after retries")
            msg = f"Chatbot request failed for {self.__class__.__name__} at {url}"
            raise ConnectorConnectionError(msg, original_error=last_exception) from last_exception

        return False, "Failed to obtain response after retries"

    def create_new_conversation(self) -> bool:
        """Create or refresh the Botlovers conversation."""
        try:
            self._initialize_conversation()
        except Exception:
            logger.exception("Failed to initialize Botlovers conversation")
            return False
        return True

    def _initialize_conversation(self) -> None:
        """Perform the handshake with Botlovers endpoints."""
        endpoints = self.get_endpoints()
        user_check = endpoints["user_check"]
        check_session = endpoints["check_session"]

        url = self.config.get_full_url(user_check.path)

        user_payload = {"data": {"accept_terminos": self.botlovers_config.accept_terminos}, "accion": "user_check"}
        user_response = self._make_request(url, user_check, user_payload) or {}

        if not isinstance(user_response, dict):
            error_msg = "Invalid user_check response"
            raise TypeError(error_msg)

        self._update_session_state(user_response)

        if not all([self.id_user, self.idweb_user, self.session_token]):
            error_msg = "Incomplete Botlovers user_check response"
            raise ValueError(error_msg)

        check_payload = {
            "data": {
                "id_user": self.id_user,
                "idweb_user": self.idweb_user,
                "session": self.session_token,
                "widget_form": self.botlovers_config.widget_form,
                "lang": self.botlovers_config.lang,
                "contexto_extra": list(self.botlovers_config.contexto_extra),
            },
            "accion": "check_session",
        }

        check_response = self._make_request(url, check_session, check_payload) or {}

        if not isinstance(check_response, dict):
            error_msg = "Invalid check_session response"
            raise TypeError(error_msg)

        self._update_session_state(check_response)
        if not self.idweb_user:
            error_msg = "Missing idweb_user after check_session"
            raise ValueError(error_msg)

        self.conversation_id = self.idweb_user
        self.latest_response = check_response

    def _update_session_state(self, response_json: dict[str, Any]) -> None:
        """Update cached identifiers and session token using response data."""
        data = response_json.get("data")
        if isinstance(data, dict):
            id_user = data.get("id_user")
            if isinstance(id_user, str) and id_user:
                self.id_user = id_user
            elif isinstance(id_user, int):
                self.id_user = str(id_user)

            idweb_user = data.get("idweb_user")
            if isinstance(idweb_user, str) and idweb_user:
                self.idweb_user = idweb_user

            session = data.get("session")
            if isinstance(session, str) and session:
                self.session_token = session

        self.session_last_updated = datetime.now(tz=UTC)
        self.latest_response = response_json

    def _refresh_session_if_needed(self) -> None:
        """Refresh the session token if it appears to be stale."""
        if not all([self.id_user, self.idweb_user, self.session_token]):
            return

        if not self._session_is_stale():
            return

        try:
            self._perform_check_session()
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("Failed to refresh Botlovers session: %s", exc)
            self._reinitialize_session()

    def _perform_check_session(self) -> None:
        """Call the check_session endpoint to refresh session data."""
        endpoints = self.get_endpoints()
        check_session = endpoints.get("check_session")
        if not check_session:
            return

        url = self.config.get_full_url(check_session.path)
        payload = {
            "data": {
                "id_user": self.id_user,
                "idweb_user": self.idweb_user,
                "session": self.session_token,
                "widget_form": self.botlovers_config.widget_form,
                "lang": self.botlovers_config.lang,
                "contexto_extra": list(self.botlovers_config.contexto_extra),
            },
            "accion": "check_session",
        }

        response = self._make_request(url, check_session, payload) or {}
        if not isinstance(response, dict):
            error_msg = "Invalid check_session response"
            raise TypeError(error_msg)

        self._update_session_state(response)
        if not self.session_token:
            error_msg = "Missing session token after check_session"
            raise ValueError(error_msg)

        self.conversation_id = self.idweb_user

    def _invalidate_session(self) -> None:
        """Invalidate cached session details to force reinitialization."""
        self.session_token = None
        self.conversation_id = None
        self.session_last_updated = None
        self.id_user = None
        self.idweb_user = None
        self.latest_response = None

    def _reinitialize_session(self) -> None:
        """Attempt to recover the session by performing a fresh handshake."""
        self._invalidate_session()
        try:
            self._initialize_conversation()
        except Exception:  # noqa: BLE001
            logger.warning("Botlovers session reinitialization failed", exc_info=True)
            self._invalidate_session()

    def _session_is_stale(self) -> bool:
        """Determine whether the session should be refreshed."""
        if self.session_last_updated is None:
            return True

        refresh_after = timedelta(seconds=self.botlovers_config.session_refresh_seconds)
        current_time = datetime.now(tz=UTC)
        return current_time - self.session_last_updated >= refresh_after
