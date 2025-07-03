from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from recipe_agent.io.nextcloud import NextcloudRecipe
from recipe_agent.recipe import Recipe


def test_recipe_nextcloud(recipe_data, output_path):
    try:
        recipe = Recipe(**recipe_data)
        for f in Recipe.model_fields:
            print(f, recipe.model_dump()[f])
    except ValidationError as exc:
        error = exc.errors()[0]
        print(repr(error['type']), error['loc'], error['msg'])
        raise ValidationError(exc)

    recipe_model_keys = [field.alias or k for k, field in Recipe.model_fields.items()]
    nextcloud_keys = recipe_data.keys()

    for key in nextcloud_keys:
        assert key in recipe_model_keys
    for model_key in recipe_model_keys:
        assert model_key in nextcloud_keys

    nextcloud_recipe = NextcloudRecipe(**recipe.model_dump())
    nextcloud_recipe.create_recipe(output_path)


def test_recipe_preview_image(output_path):
    """Test the creation of preview images for a specific Chefkoch recipe."""
    # URL des Chefkoch-Rezepts
    recipe_url = "https://www.chefkoch.de/rezepte/1382051243416986/Thai-Gurkensalat-mit-Erdnuessen-und-Chili.html"
    
    # Erstellen einer minimalen Rezeptdatenstruktur
    recipe_data = {
        "name": "Thai-Gurkensalat mit Erdnüssen und Chili",
        "url": recipe_url,
        "description": "Test für Rezeptvorschau-Bild",
        "recipeCategory": "",
        "dateCreated": datetime.today().strftime("%Y-%m-%d"),
        "dateModified": datetime.today().strftime("%Y-%m-%d")
    }
    
    # Erstellen eines Recipe-Objekts
    recipe = Recipe(**recipe_data)
    
    # Erstellen eines NextcloudRecipe-Objekts
    nextcloud_recipe = NextcloudRecipe(**recipe.model_dump())
    
    # Ordner für das spezifische Rezept erstellen
    recipe_folder = nextcloud_recipe.get_recipe_folder(output_path)
    assert recipe_folder is not None, "Rezeptordner konnte nicht erstellt werden"
    
    # Vorschaubild erstellen
    nextcloud_recipe._directory = recipe_folder
    nextcloud_recipe._create_recipe_preview_image()
    
    # Überprüfen, ob die Bilder erstellt wurden
    expected_images = ["full.jpg", "thumb.jpg", "thumb16.jpg"]
    for img_name in expected_images:
        img_path = recipe_folder / img_name
        assert img_path.exists(), f"Bild {img_name} wurde nicht erstellt"
        assert img_path.stat().st_size > 0, f"Bild {img_name} ist leer"

    assert len(nextcloud_recipe.image_url) > 10
    assert len(nextcloud_recipe.image) > 10
    
    print(f"Vorschaubilder wurden erfolgreich in {recipe_folder} erstellt")
