from conftest import URLS

from recipe_agent.utils import get_link_preview_image_url


def test_get_link_preview_image():
    image_url = get_link_preview_image_url(URLS["chilinudeln_in_erdnusssose"])
    assert image_url is not None
