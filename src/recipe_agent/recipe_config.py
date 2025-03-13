from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode, LLMExtractionStrategy

from recipe_agent.recipe import RecipeLLM


BASE_BROWSER = BrowserConfig(
    browser_type="chromium",
    headless=True,
    text_mode=True
)
LLM_PROVIDER="ollama/phi4"
# LLM_CONFIG = LLMConfig(provider=LLM_PROVIDER)
LL_EXTRACTION_STRATEGY = LLMExtractionStrategy(
    # llm_config=LLM_CONFIG,
    provider=LLM_PROVIDER,
    extraction_type="schema",
    schema=RecipeLLM.model_json_schema(by_alias=True),
    instruction="Extract a cooking recipe from the given context.\n"
                "* we need a list of ingredients and their quantities\n"
                "* if there is a space between units and the amount, remove it, eg.: 100 ml Water should become 100ml "
                "Water or 200 g Cream should become 200g Cream\n"
                "* ingredient units can be g, kg, l, ml, EL, TL, Stück"
                "* we need a list of instructions to prepare the recipe in a specific order\n"
                "* do not re-phrase ingredients or instructions\n"
                "* format for the time fields is PT0H30M0S\n"
                "* if information is missing in the context leave the field empty\n"
                "* make sure to fill in all fields of the JSON schema but do not make-up information, leave empty if unsure\n"
                "* fill the keywords field with words that you think would help search for the recipe\n"
                "* store all data in German language\n",
    input_format="markdown",
    extra_args={"temperature": 0.1, "max_tokens": 16384, "num_ctx": 16384},
    verbose=True
)

CRAWL_CONFIG = CrawlerRunConfig(
    extraction_strategy=LL_EXTRACTION_STRATEGY,
    word_count_threshold=1,
    exclude_external_links=True,
    cache_mode=CacheMode.ENABLED
)
