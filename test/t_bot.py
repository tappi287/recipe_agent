import pytest
from recipe_agent.agents import chat_agent
from recipe_agent.chat_history import ChatHistory


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


def test_chat_history():
    for history_length in (1, 2, 3, 4):
        print("---")
        u, h = "test_user", ChatHistory(max_history_length=history_length)

        h.add_user_message(u, "Hello", "You are a ChatBot")
        h.add_assistant_response(u, "Hey there!")
        h.add_user_message(u, "Good thank you!")
        h.add_assistant_response(u, "Cool")
        h.add_user_message(u, "one question?")

        messages = h.get_messages(u)
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "one question?"
        assert len(messages) <= history_length + 1

        h.add_assistant_response(u, "Sure")
        h.add_user_message(u, "Why is the sky blue?")
        h.add_assistant_response(u, "Physics.")
        h.add_user_message(u, "Mind-bowling.")
        h.add_assistant_response(u, "Told you")

        messages = h.get_messages(u)
        print("History Length:", history_length)
        assert messages[-1]["role"] == "assistant"
        assert messages[-1]["content"] == "Told you"
        assert len(messages) == history_length + 1
