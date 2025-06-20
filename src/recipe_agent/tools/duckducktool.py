import logging
from typing import List

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel

from recipe_agent.utils import exception_and_traceback


class SearchResultSelection(BaseModel):
    relevant_urls: List[str]
    refine_search_query: bool
    refined_search_query: str


class DuckDuckGoSearchResult(BaseModel):
    url: str
    title: str
    snippet: str

    def __str__(self):
        # Return as markdown
        return f"**[{self.title}]({self.url})**: {self.snippet}"


class DuckDuckGoSearchResults:
    def __init__(self):
        self._results: List[DuckDuckGoSearchResult] = list()

    def __add__(self, ddg_result: DuckDuckGoSearchResult):
        self._results.append(ddg_result)

    def append(self, ddg_result: DuckDuckGoSearchResult):
        self._results.append(ddg_result)

    def __len__(self):
        return len(self._results)

    def __iter__(self):
        yield from self._results

    def __str__(self):
        """ Returns a Markdown list """
        return "- " + "\n- ".join([str(r) for r in self._results])


def extract_url_parameter(url: str, parameter_name="uddg") -> str:
    """
    Extracts the value of the parameter from a given URL.

    Args:
        url (str): The full URL string.
        parameter_name (str): Name of the Parameter to extract

    Returns:
        str: The value of the parameter if it exists, otherwise an empty string.
    """
    # Parse the URL and its query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Extract the value for 'uddg', returning an empty string if not found
    return query_params.get(parameter_name, [''])[0]


def duckduckgo_search_local(query: str) -> DuckDuckGoSearchResults:
    results = DuckDuckGoSearchResults()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    }
    ddg_url = 'https://duckduckgo.com/html/'
    try:
        soup = BeautifulSoup(httpx.get(ddg_url, params={'q': query}, headers=headers).content, 'html.parser')
    except Exception as e:
        logging.error(f"Error trying to request search query at {ddg_url}: {exception_and_traceback(e)}")
        return results

    for el in soup.select('.links_main.result__body'):
        # -- Get result Link element
        a = el.select_one('.result__a')
        # -- Get result Snippet element
        snippet = el.select_one('.result__snippet')

        # -- Skip if not found
        if not a or not snippet:
            continue

        # -- Extract result url
        ddg_urld = a.get('href')
        url = extract_url_parameter(ddg_urld)

        # -- Filter ads
        ad_domain = extract_url_parameter(url, "ad_domain")
        if ad_domain:
            continue

        # -- Add result
        if ddg_urld and url:
            # -- Create Result
            results.append(DuckDuckGoSearchResult(title=a.string, url=url, snippet=snippet.text))

    return results


def search_tool(query: str):
    return str(duckduckgo_search_local(query))
