"""Tests for the LangGraph Agent Server connector."""  # noqa: INP001

from unittest import TestCase
from unittest.mock import patch

from chatbot_connectors.factory import ChatbotFactory
from chatbot_connectors.implementations.langgraph import (
    LangGraphChatbot,
    LangGraphResponseProcessor,
)


class LangGraphResponseProcessorTest(TestCase):
    """Test LangGraph response normalization."""

    def test_extracts_last_assistant_message(self) -> None:
        """Ignore non-assistant messages that follow the graph reply."""
        processor = LangGraphResponseProcessor()
        response = {
            "messages": [
                {"type": "human", "content": "Hello"},
                {"type": "ai", "content": "Hi!"},
                {"type": "tool", "content": "Tool output"},
            ]
        }

        self.assertEqual(processor.process(response), "Hi!")  # noqa: PT009

    def test_joins_text_content_blocks(self) -> None:
        """Join text blocks from multimodal assistant content."""
        processor = LangGraphResponseProcessor()
        response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {"type": "image", "url": "https://example.test/image.png"},
                        {"type": "text", "text": "world"},
                    ],
                }
            ]
        }

        self.assertEqual(processor.process(response), "Hello world")  # noqa: PT009

    def test_supports_custom_response_path(self) -> None:
        """Allow graphs to expose a plain response field instead of messages."""
        processor = LangGraphResponseProcessor("result.answer")

        self.assertEqual(processor.process({"result": {"answer": "Done"}}), "Done")  # noqa: PT009


class LangGraphChatbotTest(TestCase):
    """Test Agent Server request construction and thread lifecycle."""

    def test_configures_base_url_and_optional_api_key(self) -> None:
        """Normalize URLs and configure remote deployment authentication."""
        bot = LangGraphChatbot("https://example.test/deployment", api_key="secret")

        self.assertEqual(bot.config.base_url, "https://example.test/deployment/")  # noqa: PT009
        self.assertEqual(bot.session.headers["X-Api-Key"], "secret")  # noqa: PT009

    def test_execute_creates_thread_and_runs_graph(self) -> None:
        """Create a thread before the first stateful graph invocation."""
        bot = LangGraphChatbot("http://127.0.0.1:8101", assistant_id="chatbot")
        responses = [
            {"thread_id": "thread-1"},
            {
                "messages": [
                    {"type": "human", "content": "Hello"},
                    {"type": "ai", "content": "Hi from LangGraph"},
                ]
            },
        ]

        with patch.object(bot, "_make_request", side_effect=responses) as make_request:
            success, reply = bot.execute_with_input("Hello")

        self.assertTrue(success)  # noqa: PT009
        self.assertEqual(reply, "Hi from LangGraph")  # noqa: PT009
        self.assertEqual(bot.conversation_id, "thread-1")  # noqa: PT009
        self.assertEqual(make_request.call_count, 2)  # noqa: PT009
        create_call, run_call = make_request.call_args_list
        self.assertEqual(create_call.args[0], "http://127.0.0.1:8101/threads")  # noqa: PT009
        self.assertEqual(create_call.args[2], {})  # noqa: PT009
        self.assertEqual(run_call.args[0], "http://127.0.0.1:8101/threads/thread-1/runs/wait")  # noqa: PT009
        self.assertEqual(  # noqa: PT009
            run_call.args[2],
            {
                "assistant_id": "chatbot",
                "input": {"messages": [{"role": "user", "content": "Hello"}]},
            },
        )

    def test_new_conversation_replaces_thread(self) -> None:
        """A SENSEI session reset must create and use a fresh thread."""
        bot = LangGraphChatbot("http://127.0.0.1:8101")

        with patch.object(
            bot,
            "_make_request",
            side_effect=[{"thread_id": "thread-1"}, {"thread_id": "thread-2"}],
        ):
            first_created = bot.create_new_conversation()
            first_thread = bot.conversation_id
            second_created = bot.create_new_conversation()

        self.assertTrue(first_created)  # noqa: PT009
        self.assertTrue(second_created)  # noqa: PT009
        self.assertEqual(first_thread, "thread-1")  # noqa: PT009
        self.assertEqual(bot.conversation_id, "thread-2")  # noqa: PT009

    def test_connector_is_registered(self) -> None:
        """Expose LangGraph through the public connector factory."""
        self.assertIn("langgraph", ChatbotFactory.get_available_types())  # noqa: PT009
