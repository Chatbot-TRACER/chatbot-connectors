# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2025-10-14

- Renamed the Botslovers connector (previously Botlovers) and simplified its configuration to require only the base URL.

## [0.5.0] - 2025-10-13

### Added

- Metro Madrid connector covering API client, registry wiring, and CLI exposure

## [0.4.0] - 2025-10-09

### Added

- Botslovers connector with automatic session management and response parsing (supports nested messages, quick replies, GPT fallbacks)
- CLI/registry updates to expose the Botslovers connector
- README section summarising built-in connectors, example endpoints for Botslovers (Arthur/Alcampo) and MillionBot deployments

### Fixed

- Botslovers retry logic now re-establishes sessions when the backend closes idle conversations
- Response processor compatibility with Botslovers variants that return flat message lists (e.g., Arthur)

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

[Unreleased]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.2.0...v0.4.0
[0.2.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Chatbot-TRACER/chatbot-connectors/releases/tag/v0.1.0
