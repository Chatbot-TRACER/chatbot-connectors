"""Chatbot implementation modules."""

from .botlovers import BotloversChatbot
from .custom import CustomChatbot
from .metro_madrid import MetroMadridChatbot
from .millionbot import MillionBot
from .rasa import RasaChatbot
from .taskyto import ChatbotTaskyto

__all__ = [
    "BotloversChatbot",
    "ChatbotTaskyto",
    "CustomChatbot",
    "MetroMadridChatbot",
    "MillionBot",
    "RasaChatbot",
]
