"""Chatbot implementation modules."""

from .botslovers import BotsloversChatbot
from .custom import CustomChatbot
from .metro_madrid import MetroMadridChatbot
from .millionbot import MillionBot
from .rasa import RasaChatbot
from .taskyto import ChatbotTaskyto

__all__ = [
    "BotsloversChatbot",
    "ChatbotTaskyto",
    "CustomChatbot",
    "MetroMadridChatbot",
    "MillionBot",
    "RasaChatbot",
]
