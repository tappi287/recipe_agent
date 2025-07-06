"""
Tests für den NextcloudCookbookAPI Wrapper

Diese Tests decken die wesentlichen Funktionen der NextcloudCookbookAPI-Klasse ab,
einschließlich der GET, PUT und POST Methoden für den Endpunkt /api/v1/recipes.
"""
import asyncio
import os
import json
from datetime import datetime
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import httpx
import dotenv

from recipe_agent.io.nextcloud import NextcloudRecipe
from recipe_agent.io.cookbook_api import NextcloudCookbookAPI, upload_recipe
from recipe_agent.recipe import Recipe


@pytest.mark.skip("To be tested manually")
@pytest.mark.asyncio
async def test_get_all_recipes_live():
    dotenv.load_dotenv()
    api = NextcloudCookbookAPI(os.getenv("NEXTCLOUD_URL"), os.getenv("NEXTCLOUD_USERNAME"), os.getenv("NEXTCLOUD_APP_PASSWORD"))
    recipes = await api.get_all_recipes()
    for recipe in recipes:
        print(recipe.get("id"), recipe.get("name"))

    assert len(recipes) > 0


@pytest.mark.skip("To be tested manually")
@pytest.mark.asyncio
async def test_upload_hello_fresh_recipe():
    from conftest import URLS
    from recipe_agent.agents.recipe_agent import scrape_recipe
    dotenv.load_dotenv()

    # Call the function with the sample recipe
    url = URLS["chilinudeln_in_erdnusssose"]
    result = await scrape_recipe(url)

    result_recipe = Recipe.model_validate(result.model_dump())
    assert result_recipe
    await asyncio.sleep(1)

    # Upload
    await upload_recipe(result_recipe)

    # Verify Recipe is now in all recipes
    api = NextcloudCookbookAPI()
    all_recipes = await api.get_all_recipes()
    assert result_recipe.name in [r.get("name") for r in all_recipes]



@pytest.fixture
def mock_env_vars():
    """Fixture zum Setzen von Umgebungsvariablen für die Tests"""
    with patch.dict(os.environ, {
        "NEXTCLOUD_URL": "https://nextcloud.example.com",
        "NEXTCLOUD_USERNAME": "testuser",
        "NEXTCLOUD_APP_PASSWORD": "testpassword"
    }):
        yield


@pytest.fixture
def sample_recipe_data():
    """Fixture mit Beispieldaten für ein Rezept"""
    return {
        "@context": "http://schema.org",
        "@type": "Recipe",
        "id": "123",
        "name": "Testrezept",
        "description": "Ein Testrezept für Unittests",
        "url": "https://example.com/recipe",
        "imageUrl": "https://example.com/recipe.jpg",
        "image": "https://example.com/recipe.jpg",
        "printImage": True,
        "prepTime": "PT0H30M0S",
        "cookTime": "PT1H30M0S",
        "totalTime": "PT2H0M0S",
        "recipeCategory": "Test",
        "keywords": "test,rezept,unittest",
        "recipeYield": 4,
        "recipeIngredient": ["Zutat 1", "Zutat 2", "Zutat 3"],
        "recipeInstructions": ["Schritt 1", "Schritt 2", "Schritt 3"],
        "nutrition": [],
        "dateCreated": "2024-07-06T12:00:00",
        "dateModified": "2024-07-06T12:00:00"
    }


@pytest.fixture
def sample_recipe(sample_recipe_data):
    """Fixture, das ein Recipe-Objekt erzeugt"""
    return Recipe(**sample_recipe_data)


@pytest.fixture
def api_client(mock_env_vars):
    """Fixture, das eine Instanz des API-Clients zurückgibt"""
    return NextcloudCookbookAPI()


class MockResponse:
    """Mock für httpx.Response Objekte"""
    def __init__(self, status_code, json_data=None, text=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text or json.dumps(json_data) if json_data else ""

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "Mock HTTP error",
                request=httpx.Request("GET", "https://example.com"),
                response=self
            )


@pytest.mark.asyncio
async def test_init(mock_env_vars):
    """Test, ob die Initialisierung korrekt funktioniert"""
    api = NextcloudCookbookAPI()
    assert api.base_url == "https://nextcloud.example.com"
    assert api.username == "testuser"
    assert api.app_password == "testpassword"
    assert api.recipes_endpoint == "https://nextcloud.example.com/index.php/apps/cookbook/api/v1/recipes"

    # Test mit expliziten Parametern
    api = NextcloudCookbookAPI(
        base_url="https://other.example.com",
        username="otheruser",
        app_password="otherpassword"
    )
    assert api.base_url == "https://other.example.com"
    assert api.username == "otheruser"
    assert api.app_password == "otherpassword"


@pytest.mark.asyncio
async def test_get_all_recipes(api_client):
    """Test für die get_all_recipes Methode"""
    mock_recipes = [
        {"id": 1, "name": "Rezept 1"},
        {"id": 2, "name": "Rezept 2"}
    ]

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = MockResponse(200, mock_recipes)
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.get_all_recipes()

        # Überprüfen, ob die Methode die erwarteten Daten zurückgibt
        assert result == mock_recipes

        # Überprüfen, ob die richtige URL aufgerufen wurde
        mock_instance.get.assert_called_once_with(api_client.recipes_endpoint)


@pytest.mark.asyncio
async def test_get_recipe(api_client, sample_recipe_data):
    """Test für die get_recipe Methode"""
    recipe_id = 123

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = MockResponse(200, sample_recipe_data)
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.get_recipe(recipe_id)

        # Überprüfen, ob die Methode die erwarteten Daten zurückgibt
        assert result == sample_recipe_data

        # Überprüfen, ob die richtige URL aufgerufen wurde
        mock_instance.get.assert_called_once_with(f"{api_client.recipes_endpoint}/{recipe_id}")


@pytest.mark.asyncio
async def test_get_recipe_not_found(api_client):
    """Test für die get_recipe Methode, wenn das Rezept nicht gefunden wird"""
    recipe_id = 999

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MockResponse(404)
        mock_instance.get.return_value = mock_response
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("GET", f"{api_client.recipes_endpoint}/{recipe_id}"),
            response=mock_response
        ))
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.get_recipe(recipe_id)

        # Überprüfen, ob die Methode None zurückgibt
        assert result is None


@pytest.mark.asyncio
async def test_create_recipe(api_client, sample_recipe, sample_recipe_data):
    """Test für die create_recipe Methode mit einem Recipe-Objekt"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post.return_value = MockResponse(201, sample_recipe_data)
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.create_recipe(sample_recipe)

        # Überprüfen, ob die Methode die erwarteten Daten zurückgibt
        assert result == sample_recipe_data

        # Überprüfen, ob post mit den richtigen Daten aufgerufen wurde
        mock_instance.post.assert_called_once()
        # Extrahiere die Argumente des ersten Aufrufs
        call_args = mock_instance.post.call_args
        assert call_args[0][0] == api_client.recipes_endpoint

        # Überprüfen, ob die JSON-Daten korrekt sind
        # Die Daten könnten in einer anderen Reihenfolge sein, daher vergleichen wir den Inhalt
        posted_data = call_args[1]['json']
        assert posted_data["name"] == sample_recipe.name
        assert posted_data["id"] == sample_recipe.id
        assert posted_data["recipeIngredient"] == sample_recipe.recipe_ingredient


@pytest.mark.asyncio
async def test_create_recipe_with_dict(api_client, sample_recipe_data):
    """Test für die create_recipe Methode mit einem Dictionary"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post.return_value = MockResponse(201, sample_recipe_data)
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.create_recipe(sample_recipe_data)

        # Überprüfen, ob die Methode die erwarteten Daten zurückgibt
        assert result == sample_recipe_data

        # Überprüfen, ob post mit den richtigen Daten aufgerufen wurde
        mock_instance.post.assert_called_once_with(api_client.recipes_endpoint, json=sample_recipe_data)


@pytest.mark.asyncio
async def test_create_recipe_error(api_client, sample_recipe):
    """Test für die create_recipe Methode bei einem Fehler"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MockResponse(400, {"error": "Bad Request"})
        mock_instance.post.return_value = mock_response
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "Bad Request",
            request=httpx.Request("POST", api_client.recipes_endpoint),
            response=mock_response
        ))
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.create_recipe(sample_recipe)

        # Überprüfen, ob die Methode None zurückgibt
        assert result is None


@pytest.mark.asyncio
async def test_update_recipe(api_client, sample_recipe, sample_recipe_data):
    """Test für die update_recipe Methode"""
    recipe_id = 123

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.put.return_value = MockResponse(204, sample_recipe_data)
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await api_client.update_recipe(recipe_id, sample_recipe)

        # Überprüfen, ob die Methode die erwarteten Daten zurückgibt
        assert result == sample_recipe_data

        # Überprüfen, ob put mit den richtigen Daten aufgerufen wurde
        mock_instance.put.assert_called_once()
        # Extrahiere die Argumente des ersten Aufrufs
        call_args = mock_instance.put.call_args
        assert call_args[0][0] == f"{api_client.recipes_endpoint}/{recipe_id}"

        # Überprüfen, ob die JSON-Daten korrekt sind und die ID überschrieben wurde
        posted_data = call_args[1]['json']
        assert posted_data["name"] == sample_recipe.name
        assert posted_data["id"] == recipe_id  # Die ID sollte auf die angegebene ID gesetzt werden
        assert posted_data["recipeIngredient"] == sample_recipe.recipe_ingredient


@pytest.mark.asyncio
async def test_to_nextcloud_recipe(api_client, sample_recipe_data):
    """Test für die to_nextcloud_recipe Methode"""
    result = await api_client.to_nextcloud_recipe(sample_recipe_data)

    # Überprüfen, ob ein NextcloudRecipe-Objekt zurückgegeben wird
    assert isinstance(result, NextcloudRecipe)
    assert result.name == sample_recipe_data["name"]
    assert result.id == sample_recipe_data["id"]
    assert result.recipe_ingredient == sample_recipe_data["recipeIngredient"]


@pytest.mark.asyncio
async def test_convert_recipe_to_dict_recipe(api_client, sample_recipe):
    """Test für die _convert_recipe_to_dict Methode mit einem Recipe-Objekt"""
    result = api_client._convert_recipe_to_dict(sample_recipe)

    # Überprüfen, ob ein Dictionary zurückgegeben wird
    assert isinstance(result, dict)
    assert result["name"] == sample_recipe.name
    assert result["id"] == sample_recipe.id
    assert result["recipeIngredient"] == sample_recipe.recipe_ingredient


@pytest.mark.asyncio
async def test_convert_recipe_to_dict_dict(api_client, sample_recipe_data):
    """Test für die _convert_recipe_to_dict Methode mit einem Dictionary"""
    result = api_client._convert_recipe_to_dict(sample_recipe_data)

    # Überprüfen, ob dasselbe Dictionary zurückgegeben wird
    assert result is sample_recipe_data


@pytest.mark.asyncio
async def test_check_credentials_valid(api_client):
    """Test für die _check_credentials Methode mit gültigen Anmeldeinformationen"""
    result = api_client._check_credentials()

    # Überprüfen, ob True zurückgegeben wird
    assert result is True


@pytest.mark.asyncio
async def test_check_credentials_invalid():
    """Test für die _check_credentials Methode mit ungültigen Anmeldeinformationen"""
    api = NextcloudCookbookAPI()
    api.base_url = str()
    result = api._check_credentials()

    # Überprüfen, ob False zurückgegeben wird
    assert result is False


@pytest.mark.asyncio
async def test_missing_credentials_get_all_recipes():
    """Test für get_all_recipes bei fehlenden Anmeldeinformationen"""
    api = NextcloudCookbookAPI()
    api.base_url = str()
    result = await api.get_all_recipes()

    # Überprüfen, ob eine leere Liste zurückgegeben wird
    assert result == []


@pytest.mark.asyncio
async def test_missing_credentials_get_recipe():
    """Test für get_recipe bei fehlenden Anmeldeinformationen"""
    api = NextcloudCookbookAPI(base_url="", username="", app_password="")
    result = await api.get_recipe(123)

    # Überprüfen, ob None zurückgegeben wird
    assert result is None


@pytest.mark.asyncio
async def test_missing_credentials_create_recipe(sample_recipe):
    """Test für create_recipe bei fehlenden Anmeldeinformationen"""
    api = NextcloudCookbookAPI(base_url="", username="", app_password="")
    result = await api.create_recipe(sample_recipe)

    # Überprüfen, ob None zurückgegeben wird
    assert result is None


@pytest.mark.asyncio
async def test_missing_credentials_update_recipe(sample_recipe):
    """Test für update_recipe bei fehlenden Anmeldeinformationen"""
    api = NextcloudCookbookAPI(base_url="", username="", app_password="")
    result = await api.update_recipe(123, sample_recipe)

    # Überprüfen, ob None zurückgegeben wird
    assert result is None
