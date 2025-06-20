import logging
import sys
import os
from datetime import datetime

import pytest

from recipe_agent.recipe import Recipe
from recipe_agent.nextcloud_webdav import get_all_recipes, create_put_recipe

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)


@pytest.mark.asyncio
async def test_get_all_recipes(output_path):
    """Test zum Abrufen aller Rezepte von Nextcloud

    Dieser Test wird nur ausgeführt, wenn die Nextcloud-Umgebungsvariablen gesetzt sind.
    """
    os.environ["NEXTCLOUD_RECIPE_FOLDER"] = output_path.as_posix()

    # Nur ausführen, wenn die Nextcloud-Konfiguration vorhanden ist
    if not all([os.getenv("NEXTCLOUD_URL"), os.getenv("NEXTCLOUD_USERNAME"), os.getenv("NEXTCLOUD_APP_PASSWORD")]):
        pytest.skip("Nextcloud-Konfiguration nicht vollständig. Test wird übersprungen.")

    recipes = await get_all_recipes()

    # Wir prüfen nur, ob die Funktion ohne Fehler ausgeführt wird und ein Ergebnis zurückgibt
    assert isinstance(recipes, list)

    # Wenn Rezepte vorhanden sind, protokollieren wir sie
    if recipes:
        logging.info(f"Anzahl gefundener Rezepte: {len(recipes)}")
        logging.info(f"Erstes Rezept: {recipes[0]['name'] if 'name' in recipes[0] else 'Kein Name verfügbar'}")


@pytest.mark.asyncio
async def test_create_put_recipe(output_path):
    """Test zum Erstellen und Hochladen eines Rezepts zu Nextcloud

    Dieser Test wird nur ausgeführt, wenn die Nextcloud-Umgebungsvariablen gesetzt sind.
    Er erstellt ein Testrezept und lädt es auf Nextcloud hoch.
    """
    os.environ["NEXTCLOUD_RECIPE_FOLDER"] = output_path.as_posix()

    # Nur ausführen, wenn die Nextcloud-Konfiguration vorhanden ist
    if not all([os.getenv("NEXTCLOUD_URL"), os.getenv("NEXTCLOUD_USERNAME"), os.getenv("NEXTCLOUD_APP_PASSWORD")]):
        pytest.skip("Nextcloud-Konfiguration nicht vollständig. Test wird übersprungen.")

    # Erstellen eines Testrezepts
    test_recipe = Recipe(
        id=999999,  # Eindeutige Test-ID
        name=f"Testrezept WebDAV {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        description="Ein Testrezept zum Testen der WebDAV-API",
        url="https://www.kochbar.de/rezept/98235/Quatsch-mit-Sosse.html",  # URL für Bildgenerierung hinzugefügt
        recipe_category="Test",
        recipe_ingredient=["Zutat 1", "Zutat 2", "Zutat 3"],
        recipe_instructions=["Schritt 1", "Schritt 2", "Schritt 3"],
        date_created=datetime.now().isoformat(),
        date_modified=datetime.now().isoformat()
    )

    # Hochladen des Rezepts mit NextcloudRecipe
    await create_put_recipe(test_recipe)

    # Wenn die Funktion ohne Exception durchläuft, gilt der Test als bestanden
    logging.info(f"Test für create_put_recipe mit NextcloudRecipe erfolgreich durchgeführt.")
