# Chatbot Connectors

[![CI](https://github.com/Chatbot-TRACER/chatbot-connectors/actions/workflows/CI.yml/badge.svg)](https://github.com/Chatbot-TRACER/chatbot-connectors/actions/workflows/CI.yml)
[![PyPI](https://img.shields.io/pypi/v/chatbot-connectors)](https://pypi.org/project/chatbot-connectors/)
[![License](https://img.shields.io/github/license/Chatbot-TRACER/chatbot-connectors)](https://github.com/Chatbot-TRACER/chatbot-connectors/blob/main/LICENSE)

A Python library for connecting to various chatbot APIs with a unified interface.

## Installation

```bash
pip install chatbot-connectors
```

## Custom YAML Connector

If there is no connector for your chatbot and you are not willing to code one,
you can use the Custom Connector.
What this one does is read a YAML file with the info and try to work that way.

To see how to build these YAML files and use them see
[CUSTOM CONNECTOR GUIDE](docs/CUSTOM_CONNECTOR_GUIDE.md),
there are also examples in the `yaml-examples` directory.

If you want to directly try one, execute this in a Python shell:

```python
from chatbot_connectors.implementations.custom import CustomChatbot

bot = CustomChatbot("yaml-examples/ada-uam.yml")
success, response = bot.execute_with_input("Hola, necesito ayuda con Moodle")
print(response)
```

## Built-in Connectors

The library ships with several ready-to-use connectors. Each connector exposes the parameters listed via `--list-connector-params` in the CLI or `get_chatbot_parameters()` in code.

### Botslovers

- Only required parameter: `base_url`.
- Base URL examples: `https://arthur.botslovers.com/`, `https://alcampo.botslovers.com/`
- Minimal Python usage:
  ```python
  from chatbot_connectors.implementations.botslovers import BotsloversChatbot

  bot = BotsloversChatbot(base_url="https://arthur.botslovers.com/")
  success, reply = bot.execute_with_input("Hi Arthur!")
  print(reply)
  ```

### Metro de Madrid

- Uses Metro Madrid's public website widget API and auto-creates a session.
- Requires a handshake that sends the first message, selects the language, and accepts the privacy policy; the connector performs this sequence automatically using the `language` parameter (`"es"` by default, accepts `"en"`).
- Example:
  ```python
  from chatbot_connectors.implementations.metro_madrid import MetroMadridChatbot

  bot = MetroMadridChatbot(language="es")
  success, reply = bot.execute_with_input("¿A qué hora cierra hoy el metro?")
  print(reply)
  ```

### MillionBot

- Requires a `bot_id`. Known deployments:
  - ADA UAM: `60a3be81f9a6b98f7659a6f9`
  - SAIC Malaga: `64e5d1af081211d24e2cfec8`
  - Madrid te cuida: `612cc0d871562c07747d3f0a`
  - Genion: `65157185ba7cc62753c7d3e2`
  - Gallo de Morón de la Frontera: `65ca19e7dbbb4e26cbeadf24`
  - Ayto. de Arucas: `660d8b37876b1f546abde807`
  - Gestri Diputación Valencia: `6141bc1e161c3d4e06ced69c`
- Quick example:
  ```python
  from chatbot_connectors.implementations.millionbot import MillionBot

  bot = MillionBot(bot_id="60a3be81f9a6b98f7659a6f9")
  success, reply = bot.execute_with_input("Hola, ¿puedes ayudarme?")
  print(reply)
  ```

### RASA

- Use the public REST webhook, e.g. `base_url="http://localhost:5005"`.
- Optional `sender_id` controls conversation tracking.

### Taskyto

- Requires the Taskyto server base URL and optional port (defaults to `5000`).
- Example: `ChatbotTaskyto(base_url="http://localhost", port=8080)`
