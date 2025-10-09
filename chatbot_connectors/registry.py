"""Setup and registration of chatbot implementations with the factory."""

from chatbot_connectors.factory import ChatbotFactory
from chatbot_connectors.implementations.custom import CustomChatbot
from chatbot_connectors.implementations.millionbot import MillionBot
from chatbot_connectors.implementations.rasa import RasaChatbot
from chatbot_connectors.implementations.taskyto import ChatbotTaskyto


def register_all_chatbots() -> None:
    """Register all available chatbot implementations with the factory."""
    ChatbotFactory.register_chatbot("rasa", RasaChatbot, description="RASA chatbot connector using REST webhook")

    ChatbotFactory.register_chatbot("millionbot", MillionBot, description="MillionBot chatbot connector")

    ChatbotFactory.register_chatbot("taskyto", ChatbotTaskyto, description="Taskyto chatbot connector")

    ChatbotFactory.register_chatbot(
        "custom", CustomChatbot, description="Custom chatbot connector configured by a YAML file"
    )


# Auto-register when module is imported
register_all_chatbots()
