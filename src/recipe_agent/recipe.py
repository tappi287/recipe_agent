import logging
import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, ValidationError
from typing import List, Optional, Union

from recipe_agent.utils import generate_recipe_uid, convert_time_str

TIME_PATTERN = re.compile(r"PT\d\d?H\d\d?M\d\d?S")


class Recipe(BaseModel):
    context: str = Field(default="http://schema.org", alias="@context")
    type_: str = Field(default="Recipe", alias="@type")
    id: int = 0
    name: str = ""
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = Field(default=str(), alias="imageUrl")
    image: Optional[str] = ""
    print_image: bool = Field(default=True, alias="printImage")
    prep_time: Optional[str] = Field(default="PT0H30M0S", alias="prepTime")
    cook_time: Optional[str] = Field(default="PT1H30M0S", alias="cookTime")
    total_time: Optional[str] = Field(default="PT2H0M0S", alias="totalTime")
    recipe_category: str = Field(..., alias="recipeCategory")
    keywords: str = ""
    recipe_yield: int = Field(default=0, alias="recipeYield")
    tool: List[str] = Field(default_factory=list)
    recipe_ingredient: List[str] = Field(default_factory=list, alias="recipeIngredient")
    recipe_instructions: List[str] = Field(default_factory=list, alias="recipeInstructions")
    nutrition: Optional[Union[List[str], dict]] = Field(default_factory=list)
    date_created: str = Field(..., alias="dateCreated")
    date_modified: str = Field(..., alias="dateModified")

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
    recipe_id = generate_recipe_uid()

    # Create a Recipe instance with the extracted fields and generated ID
    return Recipe(
        id=recipe_id,
        name=recipe_llm.name,
        description=recipe_llm.description,
        url=recipe_llm.url,
        image=recipe_llm.image_url,
        prep_time=recipe_llm.prep_time,  # Assuming default or extracting from RecipeLLM if available
        cook_time=recipe_llm.cook_time,  # Assuming default or extracting from RecipeLLM if available
        total_time=recipe_llm.total_time,  # Assuming default or extracting from RecipeLLM if available
        recipe_category="",  # Assuming default or extracting from RecipeLLM if available
        keywords=','.join(recipe_llm.keywords),  # Assuming default or extracting from RecipeLLM if available
        recipe_yield=1,  # Assuming default or extracting from RecipeLLM if available
        recipe_ingredient=recipe_llm.recipe_ingredient,
        recipe_instructions=recipe_llm.recipe_instructions,
        date_created=datetime.now().isoformat(),  # Assuming default or extracting from RecipeLLM if available
        date_modified=datetime.now().isoformat(),  # Assuming default or extracting from RecipeLLM if available
    )
