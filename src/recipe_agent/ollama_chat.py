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
