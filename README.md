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
