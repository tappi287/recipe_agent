import logging
import sys

import pytest

from conftest import URLS
from recipe_agent.agents.recipe_agent import scrape_recipe
from recipe_agent.recipe import RecipeLLM, construct_recipe_from_recipe_llm

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)


@pytest.mark.asyncio
async def test_parse_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["mozzarella_haehnchen_in_basilikum_sahnesauce"])
    assert RecipeLLM.model_validate(result)

    r = RecipeLLM(**result)
    logging.info(f"Recipe object: {r.model_dump_json(indent=4)}")
    assert construct_recipe_from_recipe_llm(r)


@pytest.mark.asyncio
async def test_parse_rind_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["rinderschmorbraten"])

    assert RecipeLLM.model_validate(result)


@pytest.mark.asyncio
async def test_parse_shiba_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["shakshuka"])

    assert RecipeLLM.model_validate(result)


@pytest.mark.asyncio
async def test_parse_hello_fresh_recipe():
    # Call the function with the sample recipe
    result = await scrape_recipe(URLS["chilinudeln_in_erdnusssose"])

    assert RecipeLLM.model_validate(result)

    recipe_llm = RecipeLLM(**result)
    assert construct_recipe_from_recipe_llm(recipe_llm)
