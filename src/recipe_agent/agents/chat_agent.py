import logging
import os

from recipe_agent.chat_history import ChatHistory
from recipe_agent.openrouter_chat import openrouter_chat_request
from recipe_agent.recipe_config import LLM_PROVIDER, SAVE_RECIPE_TERM


SYS_PROMPT_INSTRUCTIONS = """

* antworte niemals selbst mit Koch-Rezepten oder Anleitungen zum Kochen, das System erstellt mit deiner Hilfe automatisch passend formatierte Rezepte
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
SYS_PROMPT_LINK += (f"Der Benutzer kann das Kürzel {SAVE_RECIPE_TERM} senden um Rezepte permanent "
                    f"auf einer Nextcloud Instanz zu speichern.")

ERROR_RESPONSE = "Ein Fehler ist aufgetreten. Bitte versuche es später noch einmal."


def _create_sys_prompt(sys_prompt: str) -> str:
    return sys_prompt[1:] + SYS_PROMPT_INSTRUCTIONS[1:]


async def answer_message(username: str, message: str, history: ChatHistory, custom_prompt: str = None):
    try:
        message = message[:2000]
        prompt = (f"Der Benutzer {username} "
                  f"hat diese Nachricht ohne Links geschickt: "
                  f"{message}\n") if not custom_prompt else custom_prompt

        history.add_user_message(username, prompt, _create_sys_prompt(SYS_PROMPT_NO_LINK))

        response = await openrouter_chat_request(
            LLM_PROVIDER,
            history.get_messages(username),
            options={'stream': True}
        )

        history.add_assistant_response(username, response)
        return response
    except Exception as e:
        logging.error(e)
        return ERROR_RESPONSE


async def answer_message_with_link(username: str, message: str, history: ChatHistory) -> str:
    try:
        message = message[:2000]
        prompt = (f'Der Benutzer {username} hat einen Link mit Nachricht: \"{message}\" geschickt. '
                  f'Antworte sehr kurz das du dir den Link nun anschaust. Wenn die Nachricht "{SAVE_RECIPE_TERM}" enthält, '
                  f'bestätige das du das Rezept im Nextcloud Kochbuch speicherst.')
        history.add_user_message(username, prompt, _create_sys_prompt(SYS_PROMPT_LINK))

        response = await openrouter_chat_request(
            LLM_PROVIDER,
            history.get_messages(username),
            options={'stream': True}
        )

        history.add_assistant_response(username, response)
        return response
    except Exception as e:
        logging.error(e)
        return ERROR_RESPONSE
