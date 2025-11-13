import asyncio
import logging
import os
import re
import threading
import time
from typing import List

from telegram import Update, LinkPreviewOptions
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, Defaults

from recipe_agent.agents import recipe_agent, chat_agent
from recipe_agent.recipe_config import SAVE_RECIPE_TERM
from recipe_agent.chat_history import ChatHistory
from recipe_agent.utils import to_md_recipe, exception_and_traceback, escape_md_v2
from recipe_agent.web_app import start_web_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set Defaults
DEFAULTS = Defaults(
    link_preview_options=LinkPreviewOptions(is_disabled=True)
)
BOT_AI_CHAT_HISTORY = ChatHistory(max_history_length=10)


async def answer_message_with_dots(update, username, message_text, initial_message):
    # Send initial message
    answer = await update.message.reply_text(initial_message)

    # Create a task to periodically update the message with dots
    dot_task = asyncio.create_task(_add_dots(answer, initial_message))

    # Wait for the response from the chat_agent
    response = await chat_agent.answer_message(username, message_text, BOT_AI_CHAT_HISTORY)

    # Cancel the dot task
    dot_task.cancel()

    # Edit the message with the final response
    await answer.edit_text(response)


async def _add_dots(answer, initial_message: str):
    dots, start_time = 0, time.time()
    while time.time() < start_time + 20.0:
        await asyncio.sleep(1.5)
        dots = (dots + 1) % 4
        await answer.edit_text(initial_message + " " + "." * dots)


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await rezept(update, context)


async def _chat(update: Update, message_text):
    try:
        await answer_message_with_dots(update, update.effective_user.first_name or "Du", message_text,
                                       "Kurz nachdenken")
    except Exception as e:
        logging.error(f"Error requesting answer: {exception_and_traceback(e)}")
        response = (f"Keine Webadressen in der Nachricht gefunden. Sende mir Internetadressen im Format "
                    f"https://beispiel.de/dein-rezept. Versuchs einfach nochmal {update.effective_chat.first_name}")
        await update.message.reply_text(response)


async def _process_recipe(update: Update, urls: List[str], message_text: str, just_save: bool):
    username = update.effective_user.first_name or "Du"
    save: bool = True if SAVE_RECIPE_TERM in message_text or just_save else False

    if not just_save:
        # -- Respond dynamically that we are scraping
        response = await chat_agent.answer_message_with_link(
            username, message_text, BOT_AI_CHAT_HISTORY
        )
    else:
        # -- Respond static so we get quicker to save
        response = "Rezept wird abgerufen und gespeichert"

    answer = await update.message.reply_text(response)

    for url in urls:
        dot_task = asyncio.create_task(_add_dots(answer, response))

        # Extract
        try:
            recipe_obj = await recipe_agent.scrape_recipe(url, save)
        except Exception as e:
            logging.error(f"Error creating recipe: {exception_and_traceback(e)}")
            await update.message.reply_text("Etwas ist schiefgelaufen. Versuch es später nochmal!")
            dot_task.cancel()
            return

        dot_task.cancel()

        if not just_save:
            markdown_recipe = escape_md_v2(to_md_recipe(recipe_obj))
            BOT_AI_CHAT_HISTORY.add_assistant_response(username, markdown_recipe)
            await update.message.reply_markdown_v2(
                markdown_recipe
            )
        else:
            prompt = (f"Der Benutzer {username} hatte das speichern des zuletzt gesendeten Rezeptes angefragt. "
                      f"Antworte das dass Speichern nun im Hintergrund erfolgt. "
                      f"Seine Nachricht war: {message_text}")
            await update.message.reply_text(
                await chat_agent.answer_message(username, message_text, BOT_AI_CHAT_HISTORY, prompt)
            )


async def rezept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    urls, message_text = list(), str()
    if not hasattr(update, "message"):
        # Update does not contain a (new) message
        return

    if update.message.chat.type == 'group':
        pass

    if hasattr(update, 'message'):
        message_text = update.message.text or ""
        urls = re.findall(r'https?://\S+', message_text)

    save: bool = True if SAVE_RECIPE_TERM in message_text else False
    just_save = False
    if save and not urls:
        urls = BOT_AI_CHAT_HISTORY.get_last_message_with_url(update.effective_user.first_name)
        # User has seen the recipe, just save and confirm
        just_save = True

    if urls:
        await _process_recipe(update, urls, message_text, just_save)
    else:
        await _chat(update, message_text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hey! Ich bin dein RezeptBot! Schicke mir Links zu Rezepten und ich schicke dir die Zutaten und '
        f'Zubereitung ohne das Drumherum. Schreibe {SAVE_RECIPE_TERM} '
        f'dazu wenn du das Rezept speichern möchtest.'
    )


def run_telegram_bot() -> None:
    application = Application.builder().token(os.environ.get('TELEBOT_TOKEN')).defaults(DEFAULTS).build()

    # Add the /start command handler
    application.add_handler(CommandHandler('start', start))

    # Add the /rezept command handler
    application.add_handler(CommandHandler('rezept', rezept))

    # Add global message handler
    application.add_handler(MessageHandler(None, message))

    # Retry logic for initialization
    while True:
        try:
            application.run_polling(poll_interval=5.0)
        except (NetworkError, TimedOut):
            print("Network error during initialization. Retrying in 5 seconds...")
            time.sleep(5)
        else:
            break


def main() -> None:
    # Starte den Web-Server in einem separaten Thread
    web_thread = threading.Thread(target=start_web_app, daemon=True)
    web_thread.start()

    # Starte den Telegram-Bot im Hauptthread
    run_telegram_bot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped by user")
