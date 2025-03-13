import pytest
from recipe_agent.agents import chat_agent


@pytest.mark.asyncio
async def test_bot_answer():
    name = "Tester"
    message = "Hallo"

    response = await chat_agent.answer_message(name, message)
    print(response)
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_bot_answer_with_link():
    name = "Tester"
    message = "Hallo, extrahiere diesen Link! Schnell!!  https://www.chefkoch.de/rezepte/2202191353071882/Vegane-Cranberry-Kokos-Muffins.html"

    response = await chat_agent.answer_message_with_link(name, message)
    print(response)
    assert isinstance(response, str)
