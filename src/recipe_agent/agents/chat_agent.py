import os

from recipe_agent.chat_history import ChatHistory
from recipe_agent.ollama_chat import ollama_chat_request
from recipe_agent.recipe_config import LLM_PROVIDER


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

def _create_sys_prompt(sys_prompt: str) -> str:
    return sys_prompt[1:] + SYS_PROMPT_INSTRUCTIONS[1:]


async def answer_message(username: str, message: str, history: ChatHistory):
    message = message[:2000]
    prompt = (f"Der Benutzer {username} "
              f"hat diese Nachricht ohne Links geschickt: "
              f"{message}\n")

    history.add_user_message(username, prompt, _create_sys_prompt(SYS_PROMPT_NO_LINK))

    response = await ollama_chat_request(
        LLM_PROVIDER.replace('ollama/', ''),
        history.get_messages(username),
        options={'stream': True}
    )

    history.add_assistant_response(username, response)
    return response


async def answer_message_with_link(username: str, message: str, history: ChatHistory):
    message = message[:2000]
    prompt = (f'Der Benutzer {username} hat einen Link mit Nachricht: \"{message}\" geschickt. '
              f'Antworte sehr kurz das du dir den Link nun anschaust.')
    history.add_user_message(username, prompt, _create_sys_prompt(SYS_PROMPT_LINK))

    response = await ollama_chat_request(
        LLM_PROVIDER.replace('ollama/', ''),
        history.get_messages(username),
        options={'stream': True}
    )

    history.add_assistant_response(username, response)
    return response
