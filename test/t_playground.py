import time

from conftest import INPUT_PATH

HOST = "localhost"
PORT = 5090
CONFIG_PATH = INPUT_PATH.joinpath("mcp_config.json")


def test_run_mcpo_service(input_path):
    from ollama_mcpo_adapter import MCPOService

    with MCPOService(HOST, PORT, config_path=CONFIG_PATH) as service:
        print("MCPO Service ready:", service.is_ready())

        while True:
            try:
                time.sleep(2.0)
            except KeyboardInterrupt:
                pass


def test_new_mcp(input_path):
    pass