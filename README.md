Bewegt zu [https://codeberg.org/tappi/recipe_agent](https://codeberg.org/tappi/recipe_agent)
# Recipe Agent
# Projekt-Docker-Setup

Ein minimales Docker-Setup für diese Python-Anwendung.

## Voraussetzungen

- Docker
- Docker Compose

## Nutzung

So startest du die Anwendung:
The **Recipe Agent** project is designed to assist users in extracting recipe ingredients and preparation steps from web pages. By sending URLs of recipes via a Telegram bot, it retrieves structured recipe data, omitting any unnecessary content.

This tool leverages asynchronous crawling techniques to fetch content and utilizes language models for processing complex text structures. It's ideal for food enthusiasts looking to streamline their cooking experience by quickly accessing key recipe details without manual filtering.

## Installation Instructions

To set up the Recipe Agent on your system using `uv`, follow these steps:

1. **Prerequisites**:
   - Ensure Python 3.13 or later is installed.
   - Install `uv` (Python Package manager) if you haven't already:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - ensure a local Ollama service is running with the phi4 LLM.

2. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd recipe_agent
   ```

3. **Install Dependencies**:
   Use `uv` to install the required packages specified in `pyproject.toml`.
   ```bash
   uv sync
   ```

## Usage

Run the Telegram bot by executing:

```bash
uv run bot
```

### Using the Telegram Bot

- Send recipe URLs to the bot using a plain message.
- The bot will reply with structured data containing ingredients and preparation steps.

#### Required Environment Variable

The bot functionality requires a valid `TELEBOT_TOKEN`. This token authenticates your application with the Telegram API.

1. Obtain your `TELEBOT_TOKEN` from [Telegram BotFather](https://t.me/botfather).
2. Set it in your environment:
   ```bash
   export TELEBOT_TOKEN='your-telegram-bot-token'
   ```
3. Or create a `.env` file in the repository root which will be automatically loaded

---

##### OpenRouter Models verified to work with instructions
'mistralai/mistral-nemo:free' - [URL](https://openrouter.ai/mistralai/mistral-nemo:free/api)

Note: This README is based on provided files and may require additional steps depending on specific configurations.
