import json
import logging
import re

from crawl4ai import AsyncWebCrawler, CrawlResult

from recipe_agent.recipe import RecipeLLM
from recipe_agent.ollama_chat import ollama_chat_request
from recipe_agent.recipe_config import BASE_BROWSER, LL_EXTRACTION_STRATEGY, LLM_PROVIDER, CRAWL_CONFIG


async def process_with_ollama(crawled_markdown: str, url: str) -> str:
    """ Take the scraped data as markdown and extract recipe information into Recipe Schema

    :param crawled_markdown:
    :param url:
    :return:
    """
    crawled_markdown = re.sub(r"\s\||(?:\(http.*\)|(?:\[|]))", "", crawled_markdown)
    content = LL_EXTRACTION_STRATEGY.instruction
    content += f'\nUrl: {url} Context: {crawled_markdown}'
    message = {'role': 'user', 'content': content}

    logging.info(f"Message to LLM: [{len(message['content'])}] {message}")

    response = await ollama_chat_request(
        LLM_PROVIDER.replace('ollama/', ''),
        [message],
        RecipeLLM.model_json_schema(by_alias=True),
        LL_EXTRACTION_STRATEGY.extra_args,
    )

    return response


async def scrape_recipe(url):
    """ Scrape a web page for a cooking recipe and return the data structured by an LLM """
    data = None

    # Get the base url from url
    crawl_config = CRAWL_CONFIG.clone()

    # Disable LLM Extraction for now as it does not work reliably
    crawl_config.extraction_strategy = None

    if "chefkoch" in url:
        crawl_config.css_selector = 'main article'
        crawl_config.excluded_selector = 'article#recipe-comments, amg-img, amp-carousel, amp-lightbox, amp-social-share'

    async with AsyncWebCrawler(config=BASE_BROWSER) as crawler:
        result: CrawlResult = await crawler.arun(
            url=url,
            config=crawl_config
        )

        if result.success:
            if crawl_config.extraction_strategy is None:
                response = await process_with_ollama(result.markdown, url)
                img_list = result.media.get("images")
                logging.debug("Image List: %s", img_list)
            else:
                response = result.extracted_content

            # Extracted content is presumably JSON
            data = json.loads(response)
            logging.debug("Extracted items: %s", json.dumps(data, indent=4, ensure_ascii=False))
        else:
            logging.error("Error: %s", result.error_message)

    return data
