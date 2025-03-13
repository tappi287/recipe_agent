import logging

from recipe_agent.recipe import RecipeLLM, construct_recipe_from_recipe_llm


def test_recipe_llm_obj(recipe_data):
    recipe_data["image_url"] = recipe_data["image"]
    recipe_data["keywords"] = recipe_data["keywords"].split(',')
    recipe_data["recipeInstructions"] = ["Kochzeit ca. PT0H30M0S", "Insgesamt ca. PT3H30M0S"]
    recipe_llm = RecipeLLM(**recipe_data)

    logging.info(recipe_llm.model_dump_json(indent=4))
    assert RecipeLLM.model_validate(recipe_data)

    assert construct_recipe_from_recipe_llm(recipe_llm)
