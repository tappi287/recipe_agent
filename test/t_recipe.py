import logging
import sys

import pytest

from conftest import URLS
from recipe_agent.agents.recipe_agent import scrape_recipe
from recipe_agent.recipe import Recipe

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)


@pytest.mark.asyncio
async def test_parse_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["mozzarella_haehnchen_in_basilikum_sahnesauce"])
    assert Recipe.model_validate(result.model_dump())


@pytest.mark.asyncio
async def test_parse_rind_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["rinderschmorbraten"])

    assert Recipe.model_validate(result.model_dump())


@pytest.mark.asyncio
async def test_parse_shiba_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["shakshuka"])

    assert Recipe.model_validate(result.model_dump())


@pytest.mark.asyncio
async def test_parse_hello_fresh_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["chilinudeln_in_erdnusssose"])

    assert Recipe.model_validate(result.model_dump())
