"""Chatbot implementation modules."""

from .botslovers import BotsloversChatbot
from .comunidad_madrid import ComunidadMadridChatbot
from .custom import CustomChatbot
from .langgraph import LangGraphChatbot
from .metro_madrid import MetroMadridChatbot
from .millionbot import MillionBot
from .rasa import RasaChatbot
from .taskyto import ChatbotTaskyto

__all__ = [
    "BotsloversChatbot",
    "ChatbotTaskyto",
    "ComunidadMadridChatbot",
    "CustomChatbot",
    "LangGraphChatbot",
    "MetroMadridChatbot",
    "MillionBot",
    "RasaChatbot",
]
