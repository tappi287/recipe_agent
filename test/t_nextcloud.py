from pydantic import ValidationError

from recipe_agent.nextcloud import NextcloudRecipe
from recipe_agent.recipe import Recipe


def test_recipe_nextcloud(recipe_data, output_path):
    try:
        recipe = Recipe(**recipe_data)
        for f in recipe.model_fields:
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

