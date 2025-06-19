import logging
import os
from openai import OpenAI

# OpenRouter API-Konfiguration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
SITE_URL = os.environ.get('SITE_URL', 'https://yourwebsite.com')

# Client initialisieren
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def openrouter_chat_request(model: str, messages: list, res_format: dict=None, options: dict=None) -> str:
    """
    Sendet eine Anfrage an OpenRouter und gibt die Antwort zurück

    :param model: Modellname in OpenRouter-Format (z.B. 'openai/gpt-4o')
    :param messages: Liste von Nachrichten im Format [{"role": "user", "content": "..."}]
    :param res_format: JSON-Schema für die strukturierte Ausgabe
    :param options: Zusätzliche Optionen für die Anfrage
    :return: Die Antwort des Modells als String
    """
    logging.info(f"Sende Anfrage an OpenRouter: Modell={model}, Nachrichtenlänge={len(messages)}")

    # Parameter für die Anfrage vorbereiten
    params = {
        "model": model,
        "messages": messages,
    }

    # Extra Header für OpenRouter
    extra_headers = {
        "HTTP-Referer": SITE_URL,
    }

    # Wenn Formatierung gewünscht ist
    if res_format:
        title = "Formatted Response"
        if "title" in res_format:
            title = res_format.pop("title")
        # Für OpenAI/OpenRouter-kompatibles Format
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
            stream_response = client.chat.completions.create(
                **params,
                stream=True,
                extra_headers=extra_headers
            )

            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

            return full_response
        else:
            # Ohne Streaming erhalten wir die vollständige Antwort auf einmal
            completion = client.chat.completions.create(
                **params,
                extra_headers=extra_headers
            )

            # Prüfen, ob wir eine Tool-Call-Antwort haben
            if hasattr(completion.choices[0].message, 'tool_calls') and completion.choices[0].message.tool_calls:
                # Extrahieren des JSON aus dem Tool-Call
                tool_call = completion.choices[0].message.tool_calls[0]
                response = tool_call.function.arguments
                logging.info(f"Tool-Call Antwort erhalten: {response[:100]}...")
            else:
                # Andernfalls die normale Antwort verwenden
                response = completion.choices[0].message.content
                logging.info(f"Standard-Antwort erhalten: {response[:100]}...")

            return response
    except Exception as e:
        logging.error(f"Fehler bei OpenRouter-Anfrage: {e}")
        raise
