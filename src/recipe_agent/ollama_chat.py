from typing import Dict, Any

from ollama import AsyncClient, ChatResponse


async def ollama_chat_request(model: str, messages: list, res_format: dict=None, options: dict=None) -> str:
    response = str()
    async for part in await AsyncClient().chat(
        model=model,
        messages=messages,
        format=res_format,
        options=options,
        stream=True
    ):
        part: ChatResponse
        if part.get('message').get('content'):
            response += part['message']['content']

    return response


async def ollama_chat_request_with_tools(model: str, messages: list, res_format: dict=None, options: dict=None, tools: dict = None) -> Dict[str, Any]:
    async with AsyncClient() as client:
        chat_response = await client.chat(
            model=model,
            messages=messages,
            format=res_format,
            options=options,
            stream=True,
            tools=tools
        )

        # Collecting and returning a complete ChatResponse object
        full_response: Dict[str, Any] = {}
        async for part in chat_response:
            full_response.update(part)

    return full_response
