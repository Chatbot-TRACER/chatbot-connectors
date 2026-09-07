"""Tests for the Codex and Claude Code CLI agent gateway connector."""  # noqa: INP001

from unittest import TestCase
from unittest.mock import patch

from chatbot_connectors.core import RequestMethod
from chatbot_connectors.factory import ChatbotFactory
from chatbot_connectors.implementations import CliAgentGatewayChatbot as ExportedCliAgentGatewayChatbot
from chatbot_connectors.implementations.cli_agent_gateway import (
    CliAgentGatewayChatbot,
    CliAgentGatewayResponseProcessor,
)


class CliAgentGatewayResponseProcessorTest(TestCase):
    """Test gateway response extraction."""

    def test_extracts_assistant_message_content(self) -> None:
        """Extract the response field shared by the Codex and Claude services."""
        processor = CliAgentGatewayResponseProcessor()

        response = {
            "conversationId": "conversation-1",
            "message": {"role": "assistant", "content": "Gateway response"},
            "usage": None,
        }

        self.assertEqual(processor.process(response), "Gateway response")  # noqa: PT009

    def test_returns_empty_text_for_malformed_response(self) -> None:
        """Avoid leaking non-text response values to SENSEI."""
        processor = CliAgentGatewayResponseProcessor()

        self.assertEqual(processor.process({"message": {"content": None}}), "")  # noqa: PT009
        self.assertEqual(processor.process([]), "")  # noqa: PT009


class CliAgentGatewayChatbotTest(TestCase):
    """Test gateway request construction and conversation lifecycle."""

    def test_configures_base_url_and_optional_bearer_key(self) -> None:
        """Normalize the URL and map SERVICE_API_KEY to bearer authentication."""
        bot = CliAgentGatewayChatbot("http://127.0.0.1:3000", api_key="secret")

        self.assertEqual(bot.config.base_url, "http://127.0.0.1:3000/")  # noqa: PT009
        self.assertEqual(bot.session.headers["Authorization"], "Bearer secret")  # noqa: PT009
        self.assertEqual(bot.session.headers["Content-Type"], "application/json")  # noqa: PT009

    def test_exposes_gateway_health_check(self) -> None:
        """Use the health endpoint without a message payload."""
        bot = CliAgentGatewayChatbot("http://127.0.0.1:3001")

        health_endpoint = bot.get_endpoints()["health_check"]

        self.assertEqual(health_endpoint.path, "health")  # noqa: PT009
        self.assertEqual(health_endpoint.method, RequestMethod.GET)  # noqa: PT009

    def test_execute_creates_conversation_and_sends_message(self) -> None:
        """Create a gateway session before sending the first SENSEI message."""
        bot = CliAgentGatewayChatbot("http://127.0.0.1:3000")
        responses = [
            {"id": "conversation-1", "createdAt": "2026-09-07T12:00:00.000Z"},
            {
                "conversationId": "conversation-1",
                "message": {"role": "assistant", "content": "Hello from Codex"},
                "usage": None,
            },
        ]

        with patch.object(bot, "_make_request", side_effect=responses) as make_request:
            success, reply = bot.execute_with_input("Hello")

        self.assertTrue(success)  # noqa: PT009
        self.assertEqual(reply, "Hello from Codex")  # noqa: PT009
        self.assertEqual(bot.conversation_id, "conversation-1")  # noqa: PT009
        self.assertEqual(make_request.call_count, 2)  # noqa: PT009
        create_call, message_call = make_request.call_args_list
        self.assertEqual(create_call.args[0], "http://127.0.0.1:3000/conversations")  # noqa: PT009
        self.assertEqual(create_call.args[2], {})  # noqa: PT009
        self.assertEqual(  # noqa: PT009
            message_call.args[0],
            "http://127.0.0.1:3000/conversations/conversation-1/messages",
        )
        self.assertEqual(message_call.args[2], {"message": "Hello"})  # noqa: PT009

    def test_new_conversation_replaces_gateway_session(self) -> None:
        """Map a SENSEI reset to a fresh gateway conversation."""
        bot = CliAgentGatewayChatbot("http://127.0.0.1:3001")

        with patch.object(
            bot,
            "_make_request",
            side_effect=[{"id": "conversation-1"}, {"id": "conversation-2"}],
        ):
            first_created = bot.create_new_conversation()
            first_conversation = bot.conversation_id
            second_created = bot.create_new_conversation()

        self.assertTrue(first_created)  # noqa: PT009
        self.assertTrue(second_created)  # noqa: PT009
        self.assertEqual(first_conversation, "conversation-1")  # noqa: PT009
        self.assertEqual(bot.conversation_id, "conversation-2")  # noqa: PT009

    def test_rejects_conversation_response_without_an_id(self) -> None:
        """Do not construct an invalid message URL when the gateway response is malformed."""
        bot = CliAgentGatewayChatbot("http://127.0.0.1:3000")

        with patch.object(bot, "_make_request", return_value={"createdAt": "now"}):
            created = bot.create_new_conversation()

        self.assertFalse(created)  # noqa: PT009
        self.assertIsNone(bot.conversation_id)  # noqa: PT009

    def test_connector_is_registered(self) -> None:
        """Expose the gateway through the public factory used by SENSEI."""
        self.assertIn("cli_agent_gateway", ChatbotFactory.get_available_types())  # noqa: PT009
        self.assertIs(ExportedCliAgentGatewayChatbot, CliAgentGatewayChatbot)  # noqa: PT009
