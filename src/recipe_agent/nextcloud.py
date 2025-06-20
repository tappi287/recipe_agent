""" Integration for Nextcloud Cookbook """
import logging
import os
import re
import urllib
import urllib.parse
from pathlib import Path
from typing import Optional

from recipe_agent.recipe import Recipe
from recipe_agent.utils import get_link_preview_image, download_image_to_tempfile, resize_and_crop_image

IMAGE_ATTR = {"full": 1024, "thumb": 256, "thumb16": 16, }


class NextcloudRecipe(Recipe):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._directory: Optional[Path] = None

    def get_recipe_folder(self, overwrite_recipe_dir: Optional[Path] = None) -> Optional[Path]:
        return self._create_recipe_folder(overwrite_recipe_dir)

    def create_recipe(self, overwrite_recipe_dir: Optional[Path] = None):
        self._directory = self.get_recipe_folder(overwrite_recipe_dir)
        if not self._directory:
            logging.error(f"Could not create a recipe folder at {os.getenv("NEXTCLOUD_RECIPE_FOLDER", "NaN")}")
            return

        self._create_recipe_preview_image()
        self._create_recipe_data()
        logging.debug(f"Created Nextcloud Cookbook recipe files {self.name} at {self._directory}")

    def _create_recipe_folder(self, overwrite_recipe_dir: Optional[Path] = None) -> Optional[Path]:
        recipe_base_dir = overwrite_recipe_dir or os.getenv("NEXTCLOUD_RECIPE_FOLDER", str())
        try:
            recipe_base_dir = Path(recipe_base_dir)
            recipe_base_dir.mkdir(exist_ok=True)
        except OSError:
            pass

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

        if link_preview_image.startswith("/"):
            url = urllib.parse.urlparse(self.url)
            link_preview_image = f"{url.scheme}://{url.netloc}{link_preview_image}"

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
            f.write(self.model_dump_json(indent=4, by_alias=True))
