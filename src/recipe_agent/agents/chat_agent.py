import json
import logging
import os

from collections import defaultdict

from recipe_agent.ollama_chat import ollama_chat_request
from recipe_agent.recipe_config import LLM_PROVIDER

MESSAGE_HISTORY = defaultdict(list)
ASSISTANT_HISTORY = defaultdict(list)
MAX_HISTORY_LENGTH = 3

SYS_PROMPT_INSTRUCTIONS = """
* erstelle keine Rezepte
* sei locker, das ist ein junger Messenger Dienst
* falls der Benutzer bereits Nachrichten gesendet hat, halte deine Antworten kurz
"""
if os.getenv("LLM_SPECIAL_INSTRUCTIONS"):
    SYS_PROMPT_INSTRUCTIONS += os.getenv("LLM_SPECIAL_INSTRUCTIONS")

SYS_PROMPT_NO_LINK = """
Du bist ein RezeptBot und kannst aus Links zu Webseiten Rezepte extrahieren. Antworte dem Benutzer
und erkläre ihm das die letzte Nachricht keinen Link in der Form https://beispiel.com/leckeres-rezept
enthielt.
"""

SYS_PROMPT_LINK = """
Du bist ein RezeptBot und kannst aus Links zu Webseiten Rezepte extrahieren.
"""


def _update_history(username: str, message: str, response: str):
    MESSAGE_HISTORY[username].append(message)
    MESSAGE_HISTORY[username] = MESSAGE_HISTORY[username][-MAX_HISTORY_LENGTH:]
    ASSISTANT_HISTORY[username].append(response)
    ASSISTANT_HISTORY[username] = ASSISTANT_HISTORY[username][-MAX_HISTORY_LENGTH:]


def _create_sys_prompt(sys_prompt: str) -> str:
    return sys_prompt[1:] + SYS_PROMPT_INSTRUCTIONS[1:]

def _create_messages_for_ollama(username: str, message: str, system_prompt: str) -> list:
    messages = [{'role': 'system', 'content': system_prompt}]

    for msg, assistant_msg in zip(MESSAGE_HISTORY[username], ASSISTANT_HISTORY[username]):
        messages.append({'role': 'user', 'content': msg})
        messages.append({'role': 'assistant', 'content': assistant_msg})

    messages.append({'role': 'user', 'content': message})
    logging.info(f"Using messages:\n{json.dumps(messages, indent=4)}")
    return messages


async def answer_message(username: str, message: str):
    message = message[:2000]
    prompt = (f"Der Benutzer {username} "
              f"hat diese Nachricht ohne Links geschickt: "
              f"{message}\n")

    response = await ollama_chat_request(
        LLM_PROVIDER.replace('ollama/', ''),
        _create_messages_for_ollama(username, prompt, _create_sys_prompt(SYS_PROMPT_NO_LINK)),
        options={'stream': True}
    )

    _update_history(username, message, response)
    return response


async def answer_message_with_link(username: str, message: str):
    message = message[:2000]
    prompt = f"Der Benutzer {username} hat einen Link geschickt. Antworte sehr kurz das du dir den Link nun anschaust."

    response = await ollama_chat_request(
        LLM_PROVIDER.replace('ollama/', ''),
        _create_messages_for_ollama(username, prompt, _create_sys_prompt(SYS_PROMPT_LINK)),
        options={'stream': True}
    )

    _update_history(username, message, response)
    return response
