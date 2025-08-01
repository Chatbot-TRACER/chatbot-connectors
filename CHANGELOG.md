# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-07-29

### Added

- **Custom YAML Connector**: Universal chatbot connector that works with any chatbot API through YAML configuration files
  - Supports configurable HTTP methods (GET, POST, PUT, DELETE)
  - Flexible payload templating with `{user_msg}` placeholder substitution
  - Configurable response path extraction using dot notation (e.g., `data.messages.0.content`)
  - Custom headers support for authentication and API requirements
  - No-code solution for integrating new chatbot APIs

### Examples

- **Postman Echo Bot** (`yaml-examples/postman-echo.yml`): Simple echo bot for testing the Custom YAML Connector
- **1MillionBot** (`yaml-examples/millionbot.yml`): Configuration for 1MillionBot API with authentication
- **Metro Madrid** (`yaml-examples/metro-madrid.yml`): Configuration for Metro Madrid chatbot API

### Documentation

- Added comprehensive Custom YAML Connector guide (`docs/CUSTOM_CONNECTOR_GUIDE.md`)
- Updated README with Custom Connector usage examples

## [0.1.0] - 2025-01-29

### Added

- Initial release of chatbot-connectors library
- Support for RASA chatbot connector
- Support for MillionBot chatbot connector
- Support for Taskyto chatbot connector

### Features

- **RASA Connector**: Full support for RASA webhook API
- **MillionBot Connector**: Integration with MillionBot platform
- **Taskyto Connector**: Support for Taskyto chatbot API

[Unreleased]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/releases/tag/v0.1.0
