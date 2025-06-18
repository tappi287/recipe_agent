from pathlib import Path

import pytest

OUTPUT_DIR = Path(__file__).parent.joinpath("data/output")
INPUT_PATH = Path(__file__).parent.joinpath("data/input")

# Example usage:
RECIPE_DATA = {
    "@context": "http:\\\\schema.org",
    "@type": "Recipe",
    "id": 292541,
    "name": "Rindergulasch",
    "description": "Herzhafter Rindergulasch",
    "url": "https://www.chefkoch.de/rezepte/80621031403859/Kao-Pad.html",
    "image": "/Rezepte/Rindergulasch/DSC_1375.JPG",
    "prepTime": "PT0H30M0S",
    "cookTime": "PT1H30M0S",
    "totalTime": "PT2H0M0S",
    "recipeCategory": "Herzhaft",
    "keywords": "Gulasch,Hauptspeise,Abendessen,Deftig",
    "recipeYield": 4,
    "tool": [],
    "recipeIngredient": [
        "2 Karotten", "2 Zwiebeln", "1 Chilli", "3 Knoblauchzehen", "500ml Rinderfond",
        "720g Rinderbraten", "2 Paprika", "10g Paprikapulver edelsüß", "10g Paprikapulver rosenscharf",
        "Salz und Pfeffer", "200g Tomatenmark"
    ],
    "recipeInstructions": [],
    "nutrition": [],
    "dateCreated": "2024-11-23T18:21:27+00:00",
    "dateModified": "2024-11-23T18:31:53+0000",
    "printImage": True,
    "imageUrl": "/nextcloud/index.php/apps/cookbook/webapp/recipes/292541/image?size=full"
}


@pytest.fixture
def recipe_data():
    return RECIPE_DATA


@pytest.fixture
def output_path():
    return OUTPUT_DIR


@pytest.fixture
def input_path():
    return INPUT_PATH

URLS = {
    "mozzarella_haehnchen_in_basilikum_sahnesauce":
        "https://www.chefkoch.de/rezepte/1844061298739441/Mozzarella-Haehnchen-in-Basilikum-Sahnesauce.html",
    "rinderschmorbraten":
        "https://www.chefkoch.de/rezepte/1636861271240120/Rinderschmorbraten.html",
    "shakshuka":
        "https://shibaskitchen.de/shakshuka-rezept/",
    "chilinudeln_in_erdnusssose":
        "https://www.hellofresh.de/recipes/chilinudeln-in-erdnusssose-5cc1759c2cca01000d667832"
}
