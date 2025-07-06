import json
import re
from pathlib import Path

import tornado.httpserver
from jinja2 import Environment, FileSystemLoader
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

from recipe_agent.agents import chat_agent, recipe_agent
from recipe_agent.chat_history import ChatHistory
from recipe_agent.recipe_config import SAVE_RECIPE_TERM
from recipe_agent.utils import to_md_recipe

# Chat-Historie für Web-Nutzer
WEB_CHAT_HISTORIES = ChatHistory(max_history_length=10)


class MainHandler(RequestHandler):
    def get(self):
        # Render des Hauptformulars mit Jinja2
        base_path = Path(__file__).parents[2]
        env = Environment(loader=FileSystemLoader(base_path.joinpath('templates').as_posix()))
        template = env.get_template("index.html")
        self.write(template.render())


class ChatHandler(RequestHandler):
    async def post(self):
        message = self.get_argument("message", "")
        username = self.get_argument("username", "Web-Nutzer")

        # URL aus der Nachricht extrahieren
        urls = re.findall(r'https?://\S+', message)

        save: bool = True if SAVE_RECIPE_TERM in message else False
        just_save = False
        if save and not urls:
            urls = WEB_CHAT_HISTORIES.get_last_message_with_url(username)
            just_save = True

        if urls:
            # Verarbeite Rezept-URL
            try:
                recipe_obj = await recipe_agent.scrape_recipe(urls[0], save=save)
                if just_save:
                    response = f"{recipe_obj.name} gespeichert."
                    WEB_CHAT_HISTORIES.add_assistant_response(username, response)
                else:
                    markdown_recipe = to_md_recipe(recipe_obj)
                    WEB_CHAT_HISTORIES.add_user_message(username, message)
                    WEB_CHAT_HISTORIES.add_assistant_response(username, markdown_recipe)

                    # Formatiere die Antwort für das Web
                    response = markdown_recipe
            except Exception as e:
                response = f"Fehler beim Abrufen des Rezepts: {str(e)}"
        else:
            # Normale Chat-Nachricht verarbeiten
            response = await chat_agent.answer_message(username, message, WEB_CHAT_HISTORIES)

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