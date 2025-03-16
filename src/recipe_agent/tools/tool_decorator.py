# tool_decorator.py

from typing import Callable, Dict, Any, List
from functools import wraps


class ToolRegistry:
    _tools: List[Dict[str, Any]] = []

    @classmethod
    def register(cls, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            cls._tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            })
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        return cls._tools

# Usage:
@ToolRegistry.register(
    name="get_weather",
    description="Get weather information for a city",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The name of the city"
            },
            "country_code": {
                "type": "string",
                "description": "The two-letter country code"
            }
        },
        "required": ["city", "country_code"]
    }
)
async def get_weather(city: str, country_code: str):
    # Implementation here
    pass
