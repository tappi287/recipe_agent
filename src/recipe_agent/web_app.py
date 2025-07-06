import os
import json
import asyncio
from pathlib import Path

from tornado.web import RequestHandler, Application
from tornado.ioloop import IOLoop
import tornado.httpserver
from jinja2 import Environment, FileSystemLoader

from recipe_agent.agents import chat_agent, recipe_agent
from recipe_agent.chat_history import ChatHistory
from recipe_agent.utils import to_md_recipe

# Chat-Historie für Web-Nutzer
WEB_CHAT_HISTORIES = {}

class MainHandler(RequestHandler):
    def get(self):
        # Render des Hauptformulars mit Jinja2
        base_path = Path(__file__).parents[2]
        env = Environment(loader=FileSystemLoader(base_path.joinpath('templates').as_posix()))
        template = env.get_template("index.html")
        self.write(template.render())

class ChatHandler(RequestHandler):
    async def post(self):
        # Daten aus dem Formular extrahieren
        user_id = self.get_cookie("user_id", default=None)
        if not user_id:
            # Erzeuge neue Session-ID
            import uuid
            user_id = str(uuid.uuid4())
            self.set_cookie("user_id", user_id)

        message = self.get_argument("message", "")
        username = self.get_argument("username", "Web-Nutzer")

        # Stelle sicher, dass die Chat-Historie für diesen Nutzer existiert
        if user_id not in WEB_CHAT_HISTORIES:
            WEB_CHAT_HISTORIES[user_id] = ChatHistory(max_history_length=10)

        chat_history = WEB_CHAT_HISTORIES[user_id]

        # URL aus der Nachricht extrahieren
        import re
        urls = re.findall(r'https?://\S+', message)

        if urls:
            # Verarbeite Rezept-URL
            try:
                recipe_obj = await recipe_agent.scrape_recipe(urls[0], save=False)
                markdown_recipe = to_md_recipe(recipe_obj)
                chat_history.add_assistant_response(username, markdown_recipe)

                # Formatiere die Antwort für das Web
                response = markdown_recipe
            except Exception as e:
                response = f"Fehler beim Abrufen des Rezepts: {str(e)}"
        else:
            # Normale Chat-Nachricht verarbeiten
            response = await chat_agent.answer_message(username, message, chat_history)

        # Antwort zurücksenden
        self.write(json.dumps({"response": response}))

def make_app():
    return Application([
        (r"/", MainHandler),
        (r"/chat", ChatHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8888)
    print("Web-Server läuft auf http://localhost:8888")
    IOLoop.current().start()