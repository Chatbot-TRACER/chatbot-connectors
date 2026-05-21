"""MillionBot chatbot implementation."""

import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from chatbot_connectors.core import (
    Chatbot,
    ChatbotConfig,
    EndpointConfig,
    Parameter,
    Payload,
    RequestMethod,
    ResponseProcessor,
)


class MillionBotResponseProcessor(ResponseProcessor):
    """Response processor for MillionBot chatbot."""

    def process(self, response_json: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Process the MillionBot response JSON and extract messages."""
        if isinstance(response_json, list):
            # If it's a list, process each item
            text_response = ""
            for item in response_json:
                if isinstance(item, dict):
                    text_response += self._process_single_response(item)
            return text_response
        return self._process_single_response(response_json)

    def _process_single_response(self, response_json: dict[str, Any]) -> str:
        """Process a single response JSON object."""
        text_response = ""
        for answer in response_json.get("response", []):
            if "text" in answer:
                text_response += answer["text"] + "\n"
            elif "payload" in answer:
                text_response += "\n\nAVAILABLE BUTTONS:\n\n"
                if "cards" in answer["payload"]:
                    for card in answer["payload"]["cards"]:
                        if "buttons" in card:
                            text_response += self._translate_buttons(card["buttons"])
                elif "buttons" in answer["payload"]:
                    text_response += self._translate_buttons(answer["payload"]["buttons"])
        return text_response

    def _translate_buttons(self, buttons_list: list[dict[str, Any]]) -> str:
        """Translate a list of buttons to a string."""
        text_response = ""
        for button in buttons_list:
            if "text" in button:
                text_response += f"- BUTTON TEXT: {button['text']}"
            if "value" in button:
                text_response += f" LINK: {button['value']}\n"
            else:
                text_response += " LINK: <empty>\n"
        return text_response


@dataclass
class MillionBotConfig(ChatbotConfig):
    """Configuration for the MillionBot chatbot."""

    bot_id: str = ""
    api_key: str = ""
    site_url: str = "https://www.uam.es/"
    language: str = "es"
    user_language: str = "es-ES"
    platform: str = "Win32"
    country: str = "Spain"
    country_iso_code: str = "ES"
    timezone: str = "Europe/Madrid"
    ip: str = "127.0.0.1"
    integration: str = "web"
    gdpr: bool = True
    chat_session_token: str = ""


class MillionBot(Chatbot):
    """Connector for the MillionBot chatbot API."""

    def __init__(  # noqa: PLR0913
        self,
        bot_id: str,
        *,
        api_key: str = "60a3bee2e3987316fed3218f",
        site_url: str = "https://www.uam.es/",
        language: str = "es",
        user_language: str = "es-ES",
        platform: str = "Win32",
        country: str = "Spain",
        country_iso_code: str = "ES",
        timezone: str = "Europe/Madrid",
        ip: str = "127.0.0.1",
        integration: str = "web",
        gdpr: bool = True,
        chat_session_token: str = "",
        timeout: float | tuple[float, float] | None = 60,
    ) -> None:
        """Initialize the MillionBot chatbot connector."""
        config = MillionBotConfig(
            base_url="https://api.1millionbot.com/api/public/",
            bot_id=bot_id,
            api_key=api_key,
            site_url=site_url,
            language=language,
            user_language=user_language,
            platform=platform,
            country=country,
            country_iso_code=country_iso_code,
            timezone=timezone,
            ip=ip,
            integration=integration,
            gdpr=gdpr,
            chat_session_token=chat_session_token,
            timeout=timeout,
        )
        super().__init__(config)
        self.millionbot_config = config
        self.chat_session_token = chat_session_token or secrets.token_hex(32)
        self._initialize_conversation()

    @classmethod
    def get_chatbot_parameters(cls) -> list[Parameter]:
        """Return the parameters required to initialize this chatbot."""
        return [
            Parameter(
                name="bot_id",
                type="string",
                required=True,
                description="The Bot ID for the MillionBot.",
            ),
            Parameter(
                name="api_key",
                type="string",
                required=False,
                description="The public API key for the MillionBot widget.",
                default="60a3bee2e3987316fed3218f",
            ),
            Parameter(
                name="site_url",
                type="string",
                required=False,
                description="The website URL where the MillionBot widget is embedded.",
                default="https://www.uam.es/",
            ),
            Parameter(
                name="chat_session_token",
                type="string",
                required=False,
                description="Optional x-chat-session-token captured from the widget when the bot requires it.",
                default="",
            ),
        ]

    def _browser_headers(self) -> dict[str, str]:
        """Return browser-like headers expected by public MillionBot widgets."""
        parsed_site_url = urlparse(self.millionbot_config.site_url)
        origin = f"{parsed_site_url.scheme}://{parsed_site_url.netloc}" if parsed_site_url.netloc else ""
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Authorization": f"API-KEY {self.millionbot_config.api_key}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari/537.36"
            ),
        }
        if origin:
            headers["Origin"] = origin
        if self.millionbot_config.site_url:
            headers["Referer"] = self.millionbot_config.site_url
        if self.chat_session_token:
            headers["x-chat-session-token"] = self.chat_session_token
        return headers

    def _initialize_conversation(self) -> None:
        """Initialize the conversation with the MillionBot API."""
        # Step 1: Create user
        user_payload = {
            "bot": self.millionbot_config.bot_id,
            "language": self.millionbot_config.user_language,
            "platform": self.millionbot_config.platform,
            "country": self.millionbot_config.country,
            "countryData": {"isoCode": self.millionbot_config.country_iso_code, "name": self.millionbot_config.country},
            "timezone": self.millionbot_config.timezone,
            "ip": self.millionbot_config.ip,
        }
        user_headers = self._browser_headers()
        user_url = self.config.get_full_url("users")
        timeout = self._resolve_timeout(self.config.timeout)
        user_response = self.session.post(
            user_url,
            headers=user_headers,
            json=user_payload,
            timeout=timeout,
        )
        user_response.raise_for_status()
        user_data = user_response.json()
        user_id = user_data["user"]["_id"]

        # Step 2: Create conversation
        conversation_payload = {
            "bot": self.millionbot_config.bot_id,
            "user": user_id,
            "language": self.millionbot_config.language,
            "integration": self.millionbot_config.integration,
            "gdpr": self.millionbot_config.gdpr,
        }
        conversation_headers = self._browser_headers()
        conversation_url = self.config.get_full_url("conversations")
        conversation_response = self.session.post(
            conversation_url,
            headers=conversation_headers,
            json=conversation_payload,
            timeout=timeout,
        )
        conversation_response.raise_for_status()
        conversation_data = conversation_response.json()
        self.chat_session_token = conversation_response.headers.get("x-chat-session-token", self.chat_session_token)
        self.conversation_id = conversation_data["conversation"]["_id"]
        self.user_id = user_id
        self.session.headers.update(self._browser_headers())

    def get_endpoints(self) -> dict[str, EndpointConfig]:
        """Return endpoint configurations for MillionBot chatbot."""
        return {
            "send_message": EndpointConfig(path="/messages", method=RequestMethod.POST, timeout=self.config.timeout)
        }

    def get_response_processor(self) -> ResponseProcessor:
        """Return the response processor for MillionBot chatbot."""
        return MillionBotResponseProcessor()

    def prepare_message_payload(self, user_msg: str) -> Payload:
        """Prepare the payload for sending a message to MillionBot."""
        return {
            "conversation": self.conversation_id,
            "sender_type": "User",
            "sender": self.user_id,
            "bot": self.millionbot_config.bot_id,
            "language": self.millionbot_config.language,
            "url": self.millionbot_config.site_url,
            "message": {"text": user_msg},
        }

    def _requires_conversation_id(self) -> bool:
        return True

    def create_new_conversation(self) -> bool:
        """Create a new conversation for MillionBot."""
        try:
            self._initialize_conversation()
        except (ConnectionError, TimeoutError, ValueError, KeyError):
            return False
        else:
            return True
