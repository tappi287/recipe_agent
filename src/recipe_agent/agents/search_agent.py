import json
import logging
from typing import Optional

from crawl4ai import AsyncWebCrawler, CrawlResult

from recipe_agent.chat_history import ChatHistory
from recipe_agent.openrouter_chat import openrouter_chat_request
from recipe_agent.recipe_config import CRAWL_CONFIG, BASE_BROWSER
from recipe_agent.tools.duckducktool import SearchResultSelection, duckduckgo_search_local
from recipe_agent.recipe_config import LLM_PROVIDER


MAX_ITERATIONS = 4
USER = "SearchAgent"

SEARCH_SYS_PROMPT = (
    "You are a Web Search Assistant. You try to understand the meaning of the user's search query what he had "
    "in mind when formulating this query. You need to decide between two options:\n"
    "1. Select the 3 most relevant search results from the current search\n"
    "-OR-\n"
    "2. formulate a refined query of which you think will yield more relevant results\n\n"
    "Think through your decision what could the user have exactly meant with the search query.\n\n"
    "* Store your decision as a Boolean to refine or not to refine the search in the "
    "refine_search_query field\n"
    "* if you want to refine the search query, store it in the field refined_search_query\n"
)
ITERATIVE_SEARCH_HISTORY = ChatHistory(SEARCH_SYS_PROMPT)

AGENT_SYS_PROMPT = summarizer_instructions = """
<GOAL>
Generate a high-quality summary of the web search results and keep it concise / related to the user topic.
</GOAL>

<REQUIREMENTS>
When creating a NEW summary:
1. Highlight the most relevant information related to the user topic from the search results
2. Ensure a coherent flow of information

When EXTENDING an existing summary:                                                                                                                 
1. Read the existing summary and new search results carefully.                                                    
2. Compare the new information with the existing summary.                                                         
3. For each piece of new information:                                                                             
    a. If it's related to existing points, integrate it into the relevant paragraph.                               
    b. If it's entirely new but relevant, add a new paragraph with a smooth transition.                            
    c. If it's not relevant to the user topic, skip it.                                                            
4. Ensure all additions are relevant to the user's topic.                                                         
5. Verify that your final output differs from the input summary.                                                                                                                                                            
< /REQUIREMENTS >

< FORMATTING >
- Start directly with the updated summary, without preamble or titles. Do not use XML tags in the output.  
< /FORMATTING >"""
AGENT_HISTORY = ChatHistory(AGENT_SYS_PROMPT)


async def iterative_refine(query: str) -> SearchResultSelection:
    iterations = 0

    while True:
        search_results = duckduckgo_search_local(query)
        prompt = f"User search query: \"{query}\"\nResults:\n{str(search_results)}"
        ITERATIVE_SEARCH_HISTORY.add_user_message(USER, prompt)

        response = await openrouter_chat_request(LLM_PROVIDER, ITERATIVE_SEARCH_HISTORY.get_messages(USER),
                                                 options={'stream': True},
                                                 res_format=SearchResultSelection.model_json_schema())
        ITERATIVE_SEARCH_HISTORY.add_assistant_response(USER, response)

        result_response = SearchResultSelection.model_validate(json.loads(response))
        if iterations >= MAX_ITERATIONS:
            break
        iterations += 1

        if not result_response.refine_search_query:
            logging.info(f"Search completed in {iterations} iterations.")
            break
        else:
            logging.info(f"Refining search query from: "
                         f"{query} to LLM refined query: {result_response.refine_search_query}")
            query = result_response.refined_search_query

    return result_response


async def scrape_result_page(url) -> Optional[str]:
    """ Scrape a web page """
    # Get the base url from url
    crawl_config = CRAWL_CONFIG.clone()
    # Disable LLM Extraction for now as it does not work reliably
    crawl_config.extraction_strategy = None

    async with AsyncWebCrawler(config=BASE_BROWSER) as crawler:
        result: CrawlResult = await crawler.arun(url=url, config=crawl_config)

        if result.success:
            return result.markdown
        else:
            logging.error("Error: %s", result.error_message)


async def summarize_scrape_result(scraped_content: str, query: str):
    messages = [
        {'role': 'system', 'content': 'You are Web Search Assistant. Take this markdown cluttered with '
                                      'general website content and create a concise summary of the article or '
                                      'what is presented on that webpage. Ignore comments and social media '
                                      'links.\n'
                                      '* an ideal summary will not exceed 8192 tokens.\n'
                                      '* stick to the original content as much as possible\n'
                                      '* if the content is not helpful or related to the user search query '
                                      'return the word None'},
        {'role': 'user', 'content': f"The query we are searching the Web for is: \"{query}\"\n"
                                    f"This is the extracted markdown:\n{scraped_content[:10000]}"}
    ]
    response = await openrouter_chat_request(LLM_PROVIDER, messages,
                                             options={'stream': True, "temperature": 0, "max_tokens": 8192,
                                                      # "num_ctx": 8192
                                             })
    return response


async def search_agent(query: str) -> str:
    result = await iterative_refine(query)

    for url in result.relevant_urls:
        scraped_content = await scrape_result_page(url)
        search_result_summary = await summarize_scrape_result(scraped_content, query)
        if len(search_result_summary) <= 10:
            logging.info(f"Skipping content that does not appear to be helpful.")
            continue

        prompt = (
            f"<Query>\n{query}\n<Query>\n\n"
            f"<New Search Result>\n{search_result_summary}\n<New Search Result>"
        )
        AGENT_HISTORY.add_user_message(USER, prompt)

        response = await openrouter_chat_request(LLM_PROVIDER, AGENT_HISTORY.get_messages(USER),
                                                 options={'stream': True, "temperature": 0.1, "max_tokens": 16384,
                                                          # "num_ctx": 16384
                                                          })
        AGENT_HISTORY.add_assistant_response(USER, response)

    return AGENT_HISTORY.get_messages(USER)[-1]['content']
