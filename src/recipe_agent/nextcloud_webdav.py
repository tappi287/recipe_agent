"""WebDAV Integration für Nextcloud Cookbook

Dieses Modul stellt Funktionen bereit, um mit der Nextcloud WebDAV API zu interagieren.
Es ermöglicht das Abrufen und Hochladen von Rezepten über die WebDAV-Schnittstelle.
"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from typing import List, Dict

import httpx

from recipe_agent.recipe import Recipe
from recipe_agent import nextcloud

# Konfiguration aus Umgebungsvariablen
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME")
NEXTCLOUD_APP_PASSWORD = os.getenv("NEXTCLOUD_APP_PASSWORD")
NEXTCLOUD_REMOTE_RECIPE_FOLDER = os.getenv("NEXTCLOUD_REMOTE_RECIPE_FOLDER", "Recipes")

# WebDAV Basis-URL für den Benutzer
WEBDAV_BASE_URL = f"{NEXTCLOUD_URL}/remote.php/dav/files/{NEXTCLOUD_USERNAME}/" if NEXTCLOUD_URL and NEXTCLOUD_USERNAME else ""

# Namespace für WebDAV XML-Parsing
DAV_NS = {'d': 'DAV:'}


async def get_all_recipes() -> List[Dict]:
    """Ruft alle Rezepte von Nextcloud ab

    Diese Funktion verwendet die WebDAV API, um alle recipe.json Dateien aus den Unterordnern des
    NEXTCLOUD_REMOTE_RECIPE_FOLDER zu finden und herunterzuladen. Dabei wird PROPFIND verwendet,
    um zunächst die verfügbaren Dateien zu finden, und anschließend werden sie per GET heruntergeladen.
    Die Größe der Dateien wird während des PROPFIND-Schritts ebenfalls abgefragt und protokolliert.

    Returns:
        Eine Liste von Dictionaries mit den Rezeptdaten
    """
    if not all([NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_APP_PASSWORD]):
        logging.error("Nextcloud-Konfiguration ist unvollständig. Bitte prüfen Sie Ihre .env-Datei.")
        return []

    recipes: List[Dict] = []
    async with httpx.AsyncClient(auth=(NEXTCLOUD_USERNAME, NEXTCLOUD_APP_PASSWORD)) as client:
        # Die URL für den PROPFIND-Request (der übergeordnete Ordner, der die Rezeptordner enthält)
        propfind_url = f"{WEBDAV_BASE_URL}{NEXTCLOUD_REMOTE_RECIPE_FOLDER}/"

        # PROPFIND Body, um spezifische Eigenschaften zu erhalten, inklusive der Dateigröße
        # Depth: infinity ist notwendig, um rekursiv in Unterordnern nach recipe.json zu suchen
        propfind_body = """<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:getcontentlength/>
    <d:getlastmodified/>
    <d:resourcetype/>
  </d:prop>
</d:propfind>"""

        logging.info(f"Sende PROPFIND-Anfrage an {propfind_url} auf Nextcloud...")
        try:
            response = await client.request(
                "PROPFIND",
                propfind_url,
                headers={"Depth": "infinity", "Content-Type": "application/xml"},
                content=propfind_body
            )
            response.raise_for_status()

            # PROPFIND-Antwort parsen
            root = ET.fromstring(response.text)
            for response_elem in root.findall('d:response', DAV_NS):
                href_elem = response_elem.find('d:href', DAV_NS)
                propstat_elem = response_elem.find('d:propstat', DAV_NS)

                if href_elem is None or propstat_elem is None:
                    continue

                href = href_elem.text
                # Prüfen, ob es sich um eine Datei namens 'recipe.json' handelt und kein Ordner ist
                resource_type_elem = propstat_elem.find('d:prop', DAV_NS).find('d:resourcetype', DAV_NS)
                is_collection = resource_type_elem is not None and resource_type_elem.find('d:collection',
                                                                                           DAV_NS) is not None

                # Nextcloud WebDAV gibt HREFs oft als absoluten Pfad vom dav-Root zurück (z.B. /remote.php/dav/files/user/path/to/file.json)
                # Wir müssen sicherstellen, dass wir eine vollständige, korrekte URL zum Herunterladen haben.
                if href.endswith('/recipe.json') and not is_collection:
                    # Nextcloud's hrefs beginnen oft mit '/remote.php/dav/...'
                    full_file_url = f"{NEXTCLOUD_URL}{href}"

                    content_length_elem = propstat_elem.find('d:prop', DAV_NS).find('d:getcontentlength', DAV_NS)
                    file_size = int(content_length_elem.text) if content_length_elem is not None else -1
                    logging.info(f"  Gefunden: {href} (Größe: {file_size} Bytes)")

                    # Datei herunterladen
                    try:
                        file_response = await client.get(full_file_url)
                        file_response.raise_for_status()
                        recipe_data = json.loads(file_response.text)
                        recipes.append(recipe_data)
                    except httpx.HTTPStatusError as exc:
                        logging.error(
                            f"  Fehler beim Herunterladen von {full_file_url}: HTTP {exc.response.status_code} - {exc.response.text.strip()}")
                    except httpx.RequestError as exc:
                        logging.error(f"  Fehler bei der Anfrage für {full_file_url}: {exc}")
                    except json.JSONDecodeError as exc:
                        logging.error(f"  Fehler beim Parsen von JSON aus {full_file_url}: {exc}")

        except httpx.HTTPStatusError as exc:
            logging.error(
                f"HTTP Fehler bei PROPFIND für {exc.request.url}: HTTP {exc.response.status_code} - {exc.response.text.strip()}")
        except httpx.RequestError as exc:
            logging.error(f"Fehler bei PROPFIND-Anfrage für {exc.request.url}: {exc}")
        except ET.ParseError as exc:
            logging.error(f"Fehler beim Parsen der PROPFIND XML-Antwort: {exc}")
        except Exception as e:
            logging.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    return recipes


async def create_put_recipe(recipe_instance: Recipe):
    """Erstellt oder aktualisiert ein Rezept auf Nextcloud über die WebDAV API

    Diese Funktion konvertiert ein Recipe-Objekt in ein NextcloudRecipe-Objekt, 
    erstellt lokale Dateien und lädt die JSON-Daten auf die Nextcloud-Instanz hoch.
    Sie unterstützt sowohl die lokale Speicherung als auch die WebDAV-Upload-Funktionalität.

    Args:
        recipe_instance: Die Recipe-Instanz, die hochgeladen werden soll
    """
    if not all([NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_APP_PASSWORD]):
        logging.error("Nextcloud-Konfiguration ist unvollständig. Bitte prüfen Sie Ihre .env-Datei.")
        return

    if not recipe_instance.name:
        raise ValueError("Rezeptname darf nicht leer sein, um einen Dateipfad zu erstellen.")

    # Recipe in NextcloudRecipe umwandeln und lokale Dateien erstellen
    nextcloud_recipe = nextcloud.NextcloudRecipe(**recipe_instance.model_dump())
    del recipe_instance
    nextcloud_recipe.create_recipe()

    # 2. WebDAV-Upload unabhängig von der lokalen Speicherung durchführen
    recipe_dir = nextcloud_recipe.get_recipe_folder()
    if not recipe_dir:
        raise RuntimeError("Lokales Nextcloud Rezeptverzeichnis konnte nicht erstellt werden.")

    # Pfad zum Rezeptordner und zur JSON-Datei auf Nextcloud
    recipe_folder_path = f"{NEXTCLOUD_REMOTE_RECIPE_FOLDER}/{recipe_dir.name}"
    remote_path = f"{recipe_folder_path}/recipe.json"
    folder_url = f"{WEBDAV_BASE_URL}{recipe_folder_path}"
    upload_url = f"{WEBDAV_BASE_URL}{remote_path}"

    # Rezeptdaten in JSON konvertieren (by_alias=True stellt sicher, dass Pydantic Aliase verwendet)
    recipe_json_content = nextcloud_recipe.model_dump_json(indent=4, by_alias=True)

    logging.info(f"Versuche, Rezept '{nextcloud_recipe.name}' nach {upload_url} hochzuladen/zu aktualisieren...")

    async with httpx.AsyncClient(auth=(NEXTCLOUD_USERNAME, NEXTCLOUD_APP_PASSWORD)) as client:
        try:
            # 1. Erst den Rezeptordner erstellen mit MKCOL (Make Collection)
            logging.info(f"Erstelle Ordner: {folder_url}")
            folder_response = await client.request(
                "MKCOL",
                folder_url,
                headers={'Content-Type': 'application/xml; charset=utf-8'},
            )
            # 207 (Multi-Status) oder 201 (Created) bedeuten Erfolg, 405 (Method Not Allowed) bedeutet, der Ordner existiert bereits
            if folder_response.status_code not in [201, 204, 207, 405]:
                logging.warning(f"Unerwarteter Status beim Erstellen des Ordners: {folder_response.status_code}")
                folder_response.raise_for_status()

            # 2. Datei in den erstellten Ordner hochladen
            response = await client.put(
                upload_url,
                content=recipe_json_content.encode('utf-8'),  # JSON-String muss als Bytes gesendet werden
                headers={'Content-Type': 'application/json; charset=utf-8'},  # Wichtiger Header
            )
            response.raise_for_status()  # Löst einen HTTPStatusError für schlechte Antworten (4xx oder 5xx) aus

            if response.status_code == 201:  # 201 Created (für neue Datei)
                logging.info(f"Rezept '{recipe_instance.name}' erfolgreich erstellt.")
            elif response.status_code == 204:  # 204 No Content (für erfolgreiches Update)
                logging.info(f"Rezept '{recipe_instance.name}' erfolgreich aktualisiert.")
            else:
                logging.info(
                    f"Upload für Rezept '{recipe_instance.name}' beendet mit unerwartetem Status {response.status_code}.")

        except httpx.HTTPStatusError as exc:
            logging.error(
                f"HTTP Fehler aufgetreten für {exc.request.url}: HTTP {exc.response.status_code} - {exc.response.text.strip()}")
        except httpx.RequestError as exc:
            logging.error(f"Ein Fehler während der Anfrage aufgetreten für {exc.request.url}: {exc}")
        except Exception as e:
            logging.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")


async def upload_recipe_images(nextcloud_recipe, safe_recipe_name: str, client: httpx.AsyncClient):
    """Lädt die Vorschaubilder eines Rezepts zu Nextcloud hoch

    Diese Funktion durchsucht das lokale Verzeichnis eines NextcloudRecipe-Objekts nach Bilddateien
    und lädt diese über die WebDAV-API in den entsprechenden Rezeptordner auf Nextcloud hoch.

    Args:
        nextcloud_recipe: Die NextcloudRecipe-Instanz, deren Bilder hochgeladen werden sollen
        safe_recipe_name: Der sichere (URL-freundliche) Name des Rezeptordners auf dem Server
        client: Eine aktive httpx.AsyncClient-Instanz mit Authentifizierung
    """

    if not nextcloud_recipe._directory or not nextcloud_recipe._directory.exists():
        return

    # Durchsuche das lokale Verzeichnis nach Bildern
    for image_type in IMAGE_ATTR.keys():
        # Suche nach Bilddateien mit verschiedenen Erweiterungen
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            image_name = f"{image_type}{ext}"
            local_image_path = nextcloud_recipe._directory.joinpath(image_name)

            if local_image_path.exists():
                try:
                    # Pfad auf dem Nextcloud-Server
                    remote_image_path = f"{NEXTCLOUD_REMOTE_RECIPE_FOLDER}/{safe_recipe_name}/{image_name}"
                    upload_url = f"{WEBDAV_BASE_URL}{remote_image_path}"

                    logging.info(f"Lade Bild hoch: {local_image_path} -> {upload_url}")

                    # Bild-Inhalt lesen und hochladen
                    with open(local_image_path, "rb") as img_file:
                        image_content = img_file.read()

                    # Content-Type basierend auf Dateierweiterung bestimmen
                    content_type = "image/jpeg"
                    if ext.lower() == ".png":
                        content_type = "image/png"
                    elif ext.lower() == ".webp":
                        content_type = "image/webp"

                    # Bild hochladen
                    response = await client.put(
                        upload_url,
                        content=image_content,
                        headers={'Content-Type': content_type},
                    )
                    response.raise_for_status()

                    if response.status_code in [201, 204]:
                        logging.info(f"Bild '{image_name}' erfolgreich hochgeladen.")
                    else:
                        logging.warning(
                            f"Unerwarteter Status beim Hochladen von '{image_name}': {response.status_code}")

                except Exception as e:
                    logging.error(f"Fehler beim Hochladen des Bildes '{image_name}': {e}")

                # Sobald ein Bild für diesen Typ gefunden und hochgeladen wurde, weiter zum nächsten Typ
                break
