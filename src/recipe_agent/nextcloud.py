""" Integration for Nextcloud Cookbook """
import logging
import os
import re
from pathlib import Path
from typing import Optional

import cv2

from recipe_agent.recipe import Recipe
from recipe_agent.utils import get_link_preview_image, download_image_to_tempfile, resize_image, resize_and_crop_image

RECIPE_FOLDER = os.getenv("NEXTCLOUD_RECIPE_FOLDER", str())
IMAGE_ATTR = {
    "full": 1024,
    "thumb": 256,
    "thumb16": 16,
}


class NextcloudRecipe(Recipe):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._directory: Optional[Path] = None

    def create_recipe(self, overwrite_recipe_dir: Optional[Path] = None):
        self._directory = self._create_recipe_folder(overwrite_recipe_dir)
        if not self._directory:
            logging.error(f"Could not create a recipe folder at {RECIPE_FOLDER}")
            return

        self._create_recipe_preview_image()
        self._create_recipe_data()

    def _create_recipe_folder(self, overwrite_recipe_dir: Optional[Path] = None) -> Optional[Path]:
        recipe_base_dir = overwrite_recipe_dir or RECIPE_FOLDER
        if not Path(recipe_base_dir).exists():
            return None

        safe_name = re.sub(r'[<>:"/\\|?*]', '_', self.name)
        directory = Path(recipe_base_dir).joinpath(safe_name)
        directory.mkdir(exist_ok=True)
        return directory

    def _create_recipe_preview_image(self):
        if not self.url:
            return

        link_preview_image = get_link_preview_image(self.url)
        if not link_preview_image:
            return

        temp_file = download_image_to_tempfile(link_preview_image)
        if not temp_file:
            return

        # Resize
        for name, max_size in IMAGE_ATTR.items():
            img_name = f"{name}{temp_file.suffix}"
            recipe_img = self._directory.joinpath(img_name)
            resize_and_crop_image(temp_file, recipe_img, max_size)

    def _create_recipe_data(self):
        with open(self._directory.joinpath('recipe.json'), "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))
