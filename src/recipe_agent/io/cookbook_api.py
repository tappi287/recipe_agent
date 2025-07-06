"""
Nextcloud Cookbook API Wrapper

Diese Klasse implementiert einen Wrapper für die Nextcloud Cookbook API
basierend auf der Dokumentation: https://nextcloud.github.io/cookbook/dev/api/0.1.2/
"""

import logging
import os
from typing import List, Optional, Union, Dict, Any

import httpx
from pydantic import ValidationError

from recipe_agent.io.nextcloud import NextcloudRecipe
from recipe_agent.recipe import Recipe
from recipe_agent.utils import generate_recipe_uid


class NextcloudCookbookAPI:
    """
    API-Wrapper für die Nextcloud Cookbook API Version 0.1.2
    Implementiert GET, PUT und POST Methoden für den Endpunkt /api/v1/recipes
    """

    def __init__(self, base_url: str = None, username: str = None, app_password: str = None):
        """
        Initialisiert den API-Wrapper mit den Zugangsdaten

        Args:
            base_url: Basis-URL der Nextcloud-Instanz (ohne abschließenden Slash)
            username: Benutzername für die Nextcloud-Instanz
            app_password: App-Passwort oder Passwort für die Nextcloud-Instanz
        """
        self.base_url = base_url or os.getenv("NEXTCLOUD_URL", "")
        self.username = username or os.getenv("NEXTCLOUD_USERNAME", "")
        self.app_password = app_password or os.getenv("NEXTCLOUD_APP_PASSWORD", "")

        if not all([self.base_url, self.username, self.app_password]):
            logging.warning("Nextcloud-Konfiguration unvollständig. Stelle sicher, dass NEXTCLOUD_URL, "
                            "NEXTCLOUD_USERNAME und NEXTCLOUD_APP_PASSWORD gesetzt sind.")

        # API-Endpunkt für Rezepte
        self.recipes_endpoint = f"{self.base_url}/index.php/apps/cookbook/api/v1/recipes"

    async def get_all_recipes(self) -> List[Dict[str, Any]]:
        """
        Ruft alle verfügbaren Rezepte von der Nextcloud Cookbook API ab

        Returns:
            Eine Liste von Rezept-Metadaten als Dictionaries
        """
        if not self._check_credentials():
            return []

        async with httpx.AsyncClient(auth=(self.username, self.app_password)) as client:
            try:
                response = await client.get(self.recipes_endpoint)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logging.error(f"HTTP Fehler beim Abrufen der Rezepte: HTTP {exc.response.status_code} - {exc.response.text.strip()}")
            except httpx.RequestError as exc:
                logging.error(f"Fehler bei der Anfrage für Rezepte: {exc}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler beim Abrufen der Rezepte: {e}")

        return []

    async def get_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Ruft ein einzelnes Rezept anhand seiner ID ab

        Args:
            recipe_id: Die ID des Rezepts

        Returns:
            Das Rezept als Dictionary oder None, wenn das Rezept nicht gefunden wurde
        """
        if not self._check_credentials():
            return None

        async with httpx.AsyncClient(auth=(self.username, self.app_password)) as client:
            try:
                response = await client.get(f"{self.recipes_endpoint}/{recipe_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    logging.warning(f"Rezept mit ID {recipe_id} nicht gefunden.")
                else:
                    logging.error(f"HTTP Fehler beim Abrufen des Rezepts {recipe_id}: "
                                  f"HTTP {exc.response.status_code} - {exc.response.text.strip()}")
            except httpx.RequestError as exc:
                logging.error(f"Fehler bei der Anfrage für Rezept {recipe_id}: {exc}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler beim Abrufen des Rezepts {recipe_id}: {e}")

        return None

    async def create_recipe(self, recipe: Union[Recipe, NextcloudRecipe, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Erstellt ein neues Rezept über die API

        Args:
            recipe: Das zu erstellende Rezept als Recipe-Objekt, NextcloudRecipe-Objekt oder Dictionary

        Returns:
            Das erstellte Rezept mit seiner zugewiesenen ID oder None bei einem Fehler
        """
        if not self._check_credentials():
            return None

        # Konvertieren des Rezepts in ein Dictionary
        recipe_data = self._convert_recipe_to_dict(recipe)
        if not recipe_data:
            return None

        async with httpx.AsyncClient(auth=(self.username, self.app_password)) as client:
            try:
                response = await client.post(self.recipes_endpoint, json=recipe_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logging.error(f"HTTP Fehler beim Erstellen des Rezepts: "
                              f"HTTP {exc.response.status_code} - {exc.response.text.strip()}")
            except httpx.RequestError as exc:
                logging.error(f"Fehler bei der Anfrage zum Erstellen des Rezepts: {exc}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler beim Erstellen des Rezepts: {e}")

        return None

    async def update_recipe(self, recipe_id: str, recipe: Union[Recipe, NextcloudRecipe, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Aktualisiert ein bestehendes Rezept über die API

        Args:
            recipe_id: Die ID des zu aktualisierenden Rezepts
            recipe: Das aktualisierte Rezept als Recipe-Objekt, NextcloudRecipe-Objekt oder Dictionary

        Returns:
            Das aktualisierte Rezept oder None bei einem Fehler
        """
        if not self._check_credentials():
            return None

        # Konvertieren des Rezepts in ein Dictionary
        recipe_data = self._convert_recipe_to_dict(recipe)
        if not recipe_data:
            return None

        # Stellen sicher, dass die ID im Rezept mit der angegebenen ID übereinstimmt
        recipe_data["id"] = recipe_id

        async with httpx.AsyncClient(auth=(self.username, self.app_password)) as client:
            try:
                response = await client.put(f"{self.recipes_endpoint}/{recipe_id}", json=recipe_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    logging.warning(f"Rezept mit ID {recipe_id} nicht gefunden.")
                else:
                    logging.error(f"HTTP Fehler beim Aktualisieren des Rezepts {recipe_id}: "
                                  f"HTTP {exc.response.status_code} - {exc.response.text.strip()}")
            except httpx.RequestError as exc:
                logging.error(f"Fehler bei der Anfrage zum Aktualisieren des Rezepts {recipe_id}: {exc}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler beim Aktualisieren des Rezepts {recipe_id}: {e}")

        return None

    async def reindex(self) -> bool:
        """
        Startet den Reindexierungsprozess der Nextcloud Cookbook App

        Die Reindexierung aktualisiert den Suchindex und die Metadaten aller Rezepte.
        Dies ist nützlich nach dem Hochladen mehrerer Rezepte oder nach Änderungen
        an der Dateistruktur.

        Returns:
            bool: True, wenn die Reindexierung erfolgreich gestartet wurde, sonst False
        """
        if not self._check_credentials():
            return False

        # Endpunkt für die Reindexierung
        reindex_endpoint = f"{self.base_url}/apps/cookbook/api/v1/reindex"

        async with httpx.AsyncClient(auth=(self.username, self.app_password)) as client:
            try:
                # POST-Request ohne Payload senden
                response = await client.post(reindex_endpoint)
                response.raise_for_status()

                if response.status_code in [200, 201, 204]:
                    logging.info("Reindexierung der Rezepte erfolgreich gestartet.")
                    return True
                else:
                    logging.warning(f"Unerwarteter Status bei der Reindexierung: {response.status_code}")
                    return False

            except httpx.HTTPStatusError as exc:
                logging.error(f"HTTP Fehler bei der Reindexierung: HTTP {exc.response.status_code} - {exc.response.text.strip()}")
            except httpx.RequestError as exc:
                logging.error(f"Fehler bei der Anfrage zur Reindexierung: {exc}")
            except Exception as e:
                logging.error(f"Unerwarteter Fehler bei der Reindexierung: {e}")

        return False

    @staticmethod
    async def to_nextcloud_recipe(recipe_data: Dict[str, Any]) -> Optional[NextcloudRecipe]:
        """
        Konvertiert API-Rezeptdaten in ein NextcloudRecipe-Objekt

        Args:
            recipe_data: Rezeptdaten als Dictionary von der API

        Returns:
            Ein NextcloudRecipe-Objekt oder None bei einem Fehler
        """
        try:
            # Erstelle ein NextcloudRecipe-Objekt aus den API-Daten
            return NextcloudRecipe(**recipe_data)
        except ValidationError as e:
            logging.error(f"Fehler beim Konvertieren der API-Daten in ein NextcloudRecipe-Objekt: {e}")
            return None

    def _check_credentials(self) -> bool:
        """Überprüft, ob alle erforderlichen Zugangsdaten gesetzt sind"""
        if not all([self.base_url, self.username, self.app_password]):
            logging.error("Nextcloud-Zugangsdaten sind unvollständig. Bitte prüfen Sie Ihre Umgebungsvariablen.")
            return False
        return True

    @staticmethod
    def _convert_recipe_to_dict(recipe: Union[Recipe, NextcloudRecipe, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Konvertiert ein Rezept in ein Dictionary für die API-Anfragen"""
        if isinstance(recipe, dict):
            return recipe

        try:
            if hasattr(recipe, "model_dump"):
                # Pydantic v2
                return recipe.model_dump(by_alias=True)
            elif hasattr(recipe, "dict"):
                # Pydantic v1
                return recipe.dict(by_alias=True)
            else:
                logging.error(f"Unbekanntes Rezept-Format: {type(recipe)}")
                return None
        except Exception as e:
            logging.error(f"Fehler beim Konvertieren des Rezepts in ein Dictionary: {e}")
            return None


async def upload_recipe(recipe_instance: Recipe) -> bool:
    api = NextcloudCookbookAPI()
    existing_recipes = [Recipe(**r) for r in await api.get_all_recipes()]

    update_recipe = False
    for existing_recipe in existing_recipes:
        if existing_recipe.name == recipe_instance.name:
            recipe_instance.id = existing_recipe.id
            update_recipe = True
            break

    if update_recipe:
        # -- Update existing Recipe
        if not await api.update_recipe(recipe_instance.id, recipe_instance):
            return False
        return True
    else:
        # -- Create a new Recipe
        existing_ids = {r.id for r in existing_recipes}
        recipe_instance.id = str(generate_recipe_uid(True, existing_ids))
        if not await api.create_recipe(recipe_instance):
            return False
        return True
