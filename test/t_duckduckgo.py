import pytest

from recipe_agent.agents.search_agent import search_agent, iterative_refine
from recipe_agent.tools.duckducktool import DuckDuckGoSearchResult, duckduckgo_search_local


def test_search_entities():
    results = duckduckgo_search_local("what is a typical format to feed search results to an llm")

    # DuckDuckGoResults should be iterable
    for r in results:
        assert isinstance(r, DuckDuckGoSearchResult)

    # DuckDuckGoResults should return a length
    assert len(results) >= 10

    # DuckDuckGoResults should return a str result
    assert len(str(results)) > 100

    print("---")
    print(results)


@pytest.mark.asyncio
async def test_result_selection():
    result = await iterative_refine("What is a common format to feed LLM with Web Search Engine results?")

    print(result)


@pytest.mark.asyncio
async def test_search_agent():
    query = "What is a common format to feed LLM with Web Search Engine results?"
    agent_result = await search_agent(query)
    print(agent_result)
