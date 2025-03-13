import asyncio
import logging
import os
import re
import time
from collections import defaultdict
from typing import List

from telegram import Update, LinkPreviewOptions
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, Defaults

from recipe_agent import recipe
from recipe_agent.agents import recipe_agent, chat_agent
from recipe_agent.utils import to_md_recipe

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


JOBS = defaultdict(list)

# Set Defaults
DEFAULTS = Defaults(
    link_preview_options=LinkPreviewOptions(is_disabled=True)
)

async def answer_message_with_dots(update, username, message_text, initial_message):
    # Send initial message
    answer = await update.message.reply_text(initial_message)

    # Create a task to periodically update the message with dots
    dot_task = asyncio.create_task(_add_dots(answer, initial_message))

    # Wait for the response from the chat_agent
    response = await chat_agent.answer_message(username, message_text)

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
        logging.error(f"Error requesting answer: {e}")
        response = (f"Keine Webadressen in der Nachricht gefunden. Sende mir Internetadressen im Format "
                    f"https://beispiel.de/dein-rezept. Versuchs einfach nochmal {update.effective_chat.first_name}")
        await update.message.reply_text(response)


async def _process_recipe(update: Update, urls: List[str], message_text: str):
    response = await chat_agent.answer_message_with_link(update.effective_user.first_name or "Du", message_text)
    # initial_response = "Alles klar! Adresse(n):\n" + "\n".join(urls) + "\nSchaue ich mir an, dauert einen Moment"
    answer = await update.message.reply_text(response)

    for url in urls:
        dot_task = asyncio.create_task(_add_dots(answer, response))

        # Extract
        try:
            recipe_llm_data = await recipe_agent.scrape_recipe(url)
            recipe_obj = recipe.construct_recipe_from_recipe_llm(recipe.RecipeLLM(**recipe_llm_data))
            JOBS[update.effective_chat.id].append(recipe_obj)
        except Exception as e:
            logging.error(f"Error creating recipe: {e}")
            await update.message.reply_text("Etwas ist schiefgelaufen. Versuch es später nochmal!")
            dot_task.cancel()
            return

        dot_task.cancel()
        await update.message.reply_markdown_v2(
            to_md_recipe(recipe_obj)
        )


async def rezept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    urls, message_text = list(), str()
    if update.message.chat.type == 'group':
        pass

    if hasattr(update, 'message'):
        message_text = update.message.text or ""
        urls = re.findall(r'https?://\S+', message_text)

    if urls:
        await _process_recipe(update, urls, message_text)
    else:
        await _chat(update, message_text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hey! Ich bin dein RezeptBot! Schicke mir Links zu Rezepten und ich schicke dir die Zutaten und '
        'Zubereitung ohne das Drumherum.'
    )


def main() -> None:
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped by user")
