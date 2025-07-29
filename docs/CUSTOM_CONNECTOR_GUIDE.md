# Custom YAML Connector Guide

The Custom YAML Connector allows you to connect
to any chatbot API without writing code.
Simply create a YAML configuration file
that describes how to communicate with your chatbot's API.

## Quick Start

1. **Create a YAML configuration file**:

```yaml
name: "My Custom Bot"
base_url: "https://api.mychatbot.com"
send_message:
  path: "/chat"
  method: "POST"
  payload_template:
    message: "{user_msg}"
response_path: "response.text"
```

2. **Use it in your code** (or you can try this right now in a Python shell)

```python
from chatbot_connectors.implementations.custom import CustomChatbot

bot = CustomChatbot("yaml-examples/postman-echo.yml")
success, response = bot.execute_with_input("Hello!")
print(response)
```

or

```python
from chatbot_connectors.implementations.custom import CustomChatbot

bot = CustomChatbot("yaml-examples/ada-uam.yml")
success, response = bot.execute_with_input("Hola, necesito ayuda con Moodle")
print(response)
```

## Configuration Fields

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Friendly name for your chatbot | No |
| `base_url` | Base URL of the chatbot API | Yes |
| `send_message.path` | API endpoint path (appended to base_url) | Yes |
| `send_message.method` | HTTP method (POST, GET, PUT, DELETE) | No (default: POST) |
| `send_message.headers` | Custom headers (e.g., Authorization) | No |
| `send_message.payload_template` | JSON structure with `{user_msg}` placeholder | Yes |
| `response_path` | Dot-separated path to extract bot's reply from JSON response | Yes |

## Examples

### Simple Echo Bot (Testing)

```yaml
name: "Echo Bot"
base_url: "https://postman-echo.com"
send_message:
  path: "/post"
  method: "POST"
  payload_template:
    message: "{user_msg}"
response_path: "json.message"
```

### Bot with Authentication

```yaml
name: "Secure Bot"
base_url: "https://api.mychatbot.com"
send_message:
  path: "/chat/send"
  method: "POST"
  headers:
    Authorization: "Bearer your-api-key"
    Content-Type: "application/json"
  payload_template:
    query: "{user_msg}"
    session_id: "user123"
response_path: "response.text"
```

### Complex Nested Response

```yaml
name: "Advanced Bot"
base_url: "https://api.advancedbot.com"
send_message:
  path: "/v2/chat"
  method: "POST"
  payload_template:
    input:
      text: "{user_msg}"
      context: "general"
response_path: "data.messages.0.content"
```

### Real Example: MillionBot

```yaml
name: "Ada UAM"
base_url: "https://api.1millionbot.com"
send_message:
  path: "/api/public/messages"
  method: "POST"
  headers:
    Content-Type: "application/json"
    Authorization: "60a3bee2e3987316fed3218f"
  payload_template:
    conversation: "682ce1ce271ce860cffde0fd"
    sender_type: "User"
    sender: "682ce1cefe831160cee700ed"
    bot: "60a3be81f9a6b98f7659a6f9"
    language: "es"
    url: "https://www.uam.es/uam/tecnologias-informacion/servicios-ti/acceso-remoto-red"
    message:
      text: "{user_msg}"
response_path: "response.0.text"
```

## How `response_path` Works

The `response_path` navigates through JSON responses using dot notation:

- `"message"` → `response["message"]`
- `"data.text"` → `response["data"]["text"]`
- `"results.0.content"` → `response["results"][0]["content"]`

## Tips

- Test your configuration by running it like the examples at the top
- Use `{user_msg}` as a placeholder for the user's message in your payload
- Check your API documentation for the exact response structure to set the correct `response_path`
- Add authentication headers in the `headers` section if required

## Factory Registration

To use with the ChatbotFactory:

```python
from chatbot_connectors.factory import ChatbotFactory
from chatbot_connectors.implementations.custom import CustomChatbot

# Register the custom chatbot
ChatbotFactory.register_chatbot(
    "custom",
    CustomChatbot,
    description="Custom YAML-configured chatbot"
)

# Create using factory
bot = ChatbotFactory.create_chatbot("custom", config_path="your-config.yaml")
```
