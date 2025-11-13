import json
import logging
import os
import random
import re
import tempfile
import traceback
import urllib
from pathlib import Path
from typing import Optional, Tuple, Set, Union
from urllib.parse import urlparse

import requests
from linkpreview import link_preview
from PIL import Image

ISO_8601_TIME_PATTERN = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')


def get_link_preview_image(url) -> str:
    try:
        preview = link_preview(url)
    except Exception as e:
        logging.error(f"Error fetching link preview: {e}")
        return str()

    print(f"Title: {preview.title}")
    print(f"Description: {preview.description}")
    print(f"Image: {preview.image}")
    return preview.image


def get_link_preview_image_url(url) -> str:
    link_preview_image = get_link_preview_image(url)
    if not link_preview_image:
        return str()

    if link_preview_image.startswith("/"):
        url = urllib.parse.urlparse(url)
        link_preview_image = f"{url.scheme}://{url.netloc}{link_preview_image}"

    return link_preview_image


def download_image_to_tempfile(url: str) -> Optional[Path]:
    """
    Downloads an image from the given URL and writes it to a temporary file.
    Returns the name of the temporary file and its extension.

    Args:
        url (str): The URL of the image to download.

    Returns:
        Optional[Path]: A tuple containing the path to the temporary file and its extension.
    """
    response = requests.get(url)
    if not response.ok:
        return None

    # Parse the URL to get the file extension
    parsed_url = urlparse(url)
    file_extension = parsed_url.path.split('.')[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}', mode='wb') as tmp_file:
        tmp_file.write(response.content)
        temp_file_name = tmp_file.name

    return Path(temp_file_name)


def open_and_resize_image(image_path: Path, max_size: int = 1024) -> Tuple[Image, int, int]:
    img = Image.open(image_path)
    original_width, original_height = img.size

    # Determine the scaling factor
    if original_width > max_size or original_height > max_size:
        if original_width > original_height:
            new_width = max_size
            new_height = int((max_size / original_width) * original_height)
        else:
            new_height = max_size
            new_width = int((max_size / original_height) * original_width)

        # Resize the image
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS), new_width, new_height

    return img, original_width, original_height


def resize_and_crop_image(image_path: Path, output_path: Optional[Path] = None, max_size: int = 172) -> Tuple[
    Path, int, int]:
    """
    Resizes an image such that the longest side is no longer than max_size pixels and then crops it to a square shape from the center.

    Args:
        image_path (Path): The path to the input image file.
        output_path (Path): Optional output path to write result to
        max_size (int): The maximum size for the longest side of the image. Default is 172.

    Returns:
        Tuple[str, int, int]: A tuple containing the path to the cropped image,
                              the new width, and the new height.
    """
    # Read the image
    resized_img, new_width, new_height = open_and_resize_image(image_path, max_size)

    # Crop to a square shape from the center
    min_dimension = min(new_width, new_height)
    left = (new_width - min_dimension) // 2
    top = (new_height - min_dimension) // 2
    right = (new_width + min_dimension) // 2
    bottom = (new_height + min_dimension) // 2
    cropped_img = resized_img.crop((left, top, right, bottom))

    # Save the cropped image to a new file
    output_path = output_path or image_path.with_name(f"Resized_{image_path.name}")
    cropped_img.save(output_path)

    return output_path, min_dimension, min_dimension


def resize_image(image_path: Path, output_path: Optional[Path] = None, max_size: int = 1024) -> Tuple[Path, int, int]:
    """
    Resizes an image such that the longest side is no longer than max_size pixels.

    Args:
        image_path (Path): The path to the input image file.
        output_path (Path): Optional output path to write result to
        max_size (int): The maximum size for the longest side of the image. Default is 1024.

    Returns:
        Tuple[Path, int, int]: A tuple containing the path to the resized image,
                              the new width, and the new height.
    """
    # Read the image
    resized_img, new_width, new_height = open_and_resize_image(image_path, max_size)

    # Save the resized image to a new file
    output_path = output_path or image_path.with_name(f"Resized_{image_path.name}")
    resized_img.save(output_path)

    return output_path, new_width, new_height


def convert_time_str(time_str: str):
    """ Timestring in the format PT0H30M0S to eg. 1h 30m """
    match = re.match(ISO_8601_TIME_PATTERN, time_str)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration string: {time_str}")

    # Extract hours, minutes, and seconds from the match groups
    hours, minutes, seconds = match.groups(default='0')

    # Convert extracted values to integers
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    # Build the human-readable duration string
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return ' '.join(parts)


def get_recipes_folder() -> Path:
    return Path(os.getenv("NEXTCLOUD_RECIPE_FOLDER", str()))


def get_recipe_files():
    files = list()
    try:
        for d in get_recipes_folder().iterdir():
            if d.is_dir():
                for f in d.glob('*.json'):
                    files.append(f)
    except Exception as e:
        logging.error(f"Error getting recipe files: {exception_and_traceback(e)}")

    return files


def parse_recipe(file: Path) -> dict:
    try:
        with open(file, 'rb') as f:
            data = json.load(f)
        return data
    except Exception:
        return dict()


def generate_recipe_uid(use_nextcloud_recipe_filestore: bool = False, existing_ids: Set[Union[int, str]] = None) -> int:
    existing_ids = [str(i) for i in existing_ids or set()]
    if use_nextcloud_recipe_filestore:
        for file in get_recipe_files():
            recipe_data = parse_recipe(file)
            existing_ids.add(int(recipe_data.get("id", 0)))

    new_id = random.randint(100000, 999999)
    while str(new_id) in existing_ids:
        new_id = random.randint(100000, 999999)

    return new_id


def escape_md_v2(txt: str):
    for c in ('_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'):
        txt = txt.replace(c, f"\\{c}")
    return txt


def to_md_recipe(r: 'Recipe'):
    md = f"## {escape_md_v2(r.name)}\n\n"
    md += f"#### Zutaten\n   \\- "
    md += "\n   \\- ".join([escape_md_v2(i) for i in r.recipe_ingredient])
    md += "\n\n#### Zubereitung\n"
    md += "\n".join([escape_md_v2(f"{idx + 1: 2d}. {i}") for idx, i in enumerate(r.recipe_instructions)])

    return md


def to_telegram_md_recipe(r: 'Recipe'):
    md = f"*{escape_md_v2(r.name)}*\n\n*Zutaten*\n   \\- "
    md += "\n   \\- ".join([escape_md_v2(i) for i in r.recipe_ingredient])
    md += "\n\n*Zubereitung*\n"
    md += "\n".join([escape_md_v2(f"{idx + 1: 2d}. {i}") for idx, i in enumerate(r.recipe_instructions)])

    return md


def exception_and_traceback(e):
    try:
        return "\n".join(traceback.format_exception(e))
    except Exception as _e:
        return f"{_e}\n{e}"
