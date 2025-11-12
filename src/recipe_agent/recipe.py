import logging
import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union

from recipe_agent.utils import generate_recipe_uid, convert_time_str

TIME_PATTERN = re.compile(r"PT\d\d?H\d\d?M\d\d?S")


class Nutrition(BaseModel):
    """Nutrition information according to schema.org"""
    type_: str = Field(default="NutritionInformation", alias="@type")
    calories: Optional[str] = None
    carbohydrate_content: Optional[str] = Field(default=None, alias="carbohydrateContent")
    cholesterol_content: Optional[str] = Field(default=None, alias="cholesterolContent")
    fat_content: Optional[str] = Field(default=None, alias="fatContent")
    fiber_content: Optional[str] = Field(default=None, alias="fiberContent")
    protein_content: Optional[str] = Field(default=None, alias="proteinContent")
    saturated_fat_content: Optional[str] = Field(default=None, alias="saturatedFatContent")
    serving_size: Optional[str] = Field(default=None, alias="servingSize")
    sodium_content: Optional[str] = Field(default=None, alias="sodiumContent")
    sugar_content: Optional[str] = Field(default=None, alias="sugarContent")
    trans_fat_content: Optional[str] = Field(default=None, alias="transFatContent")
    unsaturated_fat_content: Optional[str] = Field(default=None, alias="unsaturatedFatContent")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class Recipe(BaseModel):
    context: str = Field(default="http://schema.org", alias="@context")
    type_: str = Field(default="Recipe", alias="@type")
    id: str = Field(default="0")
    name: str = ""
    description: str = Field(default="")
    url: str = Field(default="")
    image_url: str = Field(default="", alias="imageUrl")
    image_placeholder_url: str = Field(default="", alias="imagePlaceholderUrl")
    image: str = Field(default="")
    prep_time: Optional[str] = Field(default=None, alias="prepTime")
    cook_time: Optional[str] = Field(default=None, alias="cookTime")
    total_time: Optional[str] = Field(default=None, alias="totalTime")
    recipe_category: str = Field(default="", alias="recipeCategory")
    keywords: Optional[str] = Field(default="")
    recipe_yield: int = Field(default=1, alias="recipeYield")
    tool: List[str] = Field(default_factory=list)
    recipe_ingredient: List[str] = Field(default_factory=list, alias="recipeIngredient")
    recipe_instructions: List[str] = Field(default_factory=list, alias="recipeInstructions")
    nutrition: Optional[Union[List, Nutrition]] = Field(default_factory=list)
    date_created: str = Field(default_factory=lambda: datetime.now().isoformat(), alias="dateCreated")
    date_modified: Optional[str] = Field(default=None, alias="dateModified")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RecipeLLM(BaseModel):
    name: str
    url: str
    image_url: str
    description: str
    recipe_ingredient: List[str] = Field(alias="recipeIngredient")
    recipe_instructions: List[str] = Field(alias="recipeInstructions")
    prep_time: str = Field(alias="prepTime")
    cook_time: str = Field(alias="cookTime")
    total_time: str = Field(alias="totalTime")
    keywords: List[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._parse_instructions()

    @classmethod
    def get_in_openai_format(cls) -> dict:
        data = cls.model_json_schema(by_alias=True)
        title = "Formatted Response"
        if "title" in data:
            data.pop("title")

        return {
            "type": "json_schema",  # json_object for deepinfra
            "json_schema": {
                "name": title,
                "strict": True,
                "schema": data
            }}

    def _parse_instructions(self):
        updated_instructions = list()

        # -- Convert time strings in instructions
        for instruction in self.recipe_instructions:
            try:
                m = re.search(TIME_PATTERN, instruction)
                if m:
                    time_str = convert_time_str(m.group())
                    instruction = instruction.replace(m.group(), time_str)
            except Exception as e:
                logging.error(f"Error parsing time string in instructions: {e}")

            updated_instructions.append(instruction)

        self.recipe_instructions = updated_instructions


def construct_recipe_from_recipe_llm(recipe_llm: RecipeLLM) -> Recipe:
    # Generate a unique ID for the recipe
    recipe_id = str(generate_recipe_uid())

    # Create a Recipe instance with the extracted fields and generated ID
    return Recipe(
        id=recipe_id,
        name=recipe_llm.name,
        description=recipe_llm.description,
        url=recipe_llm.url,
        image=recipe_llm.image_url,
        imageUrl=recipe_llm.image_url,
        imagePlaceholderUrl="",  # Default empty string as per schema
        prepTime=recipe_llm.prep_time,
        cookTime=recipe_llm.cook_time,
        totalTime=recipe_llm.total_time,
        recipeCategory="",  # Default empty string as per schema
        keywords=','.join(recipe_llm.keywords),
        recipeYield=1,  # Default value as per schema
        recipeIngredient=recipe_llm.recipe_ingredient,
        recipeInstructions=recipe_llm.recipe_instructions,
        dateCreated=datetime.now().isoformat(),
        dateModified=datetime.now().isoformat(),
    )
