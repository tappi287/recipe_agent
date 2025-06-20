import logging
import os
from litellm import completion

from recipe_agent.utils import exception_and_traceback


async def openrouter_chat_request(model: str, messages: list, res_format: dict=None, options: dict=None) -> str:
    """
    Sendet eine Anfrage an litellm und gibt die Antwort zurück

    :param model: Modellname in litellm-Format (z.B. 'openai/gpt-4o')
    :param messages: Liste von Nachrichten im Format [{"role": "user", "content": "..."}]
    :param res_format: JSON-Schema für die strukturierte Ausgabe
    :param options: Zusätzliche Optionen für die Anfrage
    :return: Die Antwort des Modells als String
    """
    logging.info(f"Sende Anfrage an litellm: Modell={model}, Nachrichtenlänge={len(messages)}")

    # Parameter für die Anfrage vorbereiten
    params = {
        "model": model,
        "messages": messages,
    }

    # Extra Header für litellm
    extra_headers = {
        "HTTP-Referer": os.environ.get('SITE_URL', 'https://yourwebsite.com')
    }

    # Wenn Formatierung gewünscht ist
    if res_format:
        title = "Formatted Response"
        if "title" in res_format:
            title = res_format.pop("title")
        # Für litellm-kompatibles Format
        openai_resformat = {
            "type": "json_schema",  # json_object for deepinfra
            "json_schema": {
                "name": title,
                "strict": True,
                "schema": res_format
            }}
        params["response_format"] = openai_resformat

    # Prüfen ob Streaming aktiviert werden soll
    stream = False
    if options and 'stream' in options:
        stream = options['stream']
        # Entfernen, da wir es separat übergeben
        if 'stream' in options:
            del options['stream']

    # Zusätzliche Optionen hinzufügen
    if options:
        for key, value in options.items():
            if key not in params:
                params[key] = value

    try:
        if stream:
            # Bei Streaming sammeln wir die Teile
            full_response = ""
            stream_response = completion(
                **params,
                stream=True,
                headers=extra_headers, input_cost_per_token=0.0, output_cost_per_token=0.0
            )

            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

            return full_response
        else:
            # Ohne Streaming erhalten wir die vollständige Antwort auf einmal
            response = completion(
                **params,
                headers=extra_headers, input_cost_per_token=0.0, output_cost_per_token=0.0
            )

            # Prüfen, ob wir eine Tool-Call-Antwort haben
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                # Extrahieren des JSON aus dem Tool-Call
                tool_call = response.choices[0].message.tool_calls[0]
                response_text = tool_call.function.arguments
                logging.info(f"Tool-Call Antwort erhalten: {response_text[:100]}...")
            else:
                # Andernfalls die normale Antwort verwenden
                response_text = response.choices[0].message.content
                logging.info(f"Standard-Antwort erhalten: {response_text[:100]}...")

            return response_text
    except Exception as e:
        logging.error(f"Fehler bei litellm-Anfrage: {exception_and_traceback(e)}")
        raise
