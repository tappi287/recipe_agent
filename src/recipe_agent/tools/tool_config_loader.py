# tool_config_loader.py
from pathlib import Path

import yaml
from typing import List, Dict, Any


def load_tool_configs() -> List[Dict[str, Any]]:
    with open(Path(__file__).parents[3] / 'data' / 'tools_config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    return [{
        "type": "function",
        "function": tool
    } for tool in config['tools']]
