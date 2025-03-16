# tool_manager.py

from typing import List, Dict, Any
from .tool_decorator import ToolRegistry
from .tool_config_loader import load_tool_configs

class ToolManager:
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        return ToolRegistry.get_all_tools() + load_tool_configs()

# Usage in your Ollama API call:
# from tool_manager import ToolManager

ollama_payload = {
    "model": "mistral",
    "messages": [
        {
            "role": "user",
            "content": "What's the weather like in London?"
        }
    ],
    "stream": False,
    "tools": ToolManager.get_all_tools()
}