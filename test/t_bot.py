import pytest
from recipe_agent.agents import chat_agent
from recipe_agent.chat_history import ChatHistory


@pytest.mark.asyncio
async def test_bot_answer():
    name = "Tester"
    message = "Hallo"

    response = await chat_agent.answer_message(name, message, ChatHistory())
    print(response)
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_bot_answer_with_link():
    name = "Tester"
    message = "Hallo, extrahiere diesen Link! Schnell!!  https://www.chefkoch.de/rezepte/2202191353071882/Vegane-Cranberry-Kokos-Muffins.html"

    response = await chat_agent.answer_message_with_link(name, message, ChatHistory())
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


def test_get_last_urls():
    history = ChatHistory()
    user = "test_user"

    # Add messages without URLs
    history.add_user_message(user, "Hello", "You are a ChatBot")
    history.add_assistant_response(user, "Hi there!")

    # No URLs should be found
    assert history.get_last_message_with_url(user) is None

    # Add message with URL
    url = "https://www.example.com/recipe"
    history.add_user_message(user, f"Check this {url}", "You are a ChatBot")

    # URL should be found
    assert history.get_last_message_with_url(user) == [url]

    # Add message without URL
    history.add_user_message(user, "Thanks!", "You are a ChatBot")

    # Previous URL should still be found
    assert history.get_last_message_with_url(user) == [url]

    # Add message with multiple URLs
    urls = ["https://example1.com", "https://example2.com"]
    history.add_user_message(user, f"Multiple links {urls[0]} and {urls[1]}", "You are a ChatBot")

    # Both URLs should be found
    assert history.get_last_message_with_url(user) == urls
