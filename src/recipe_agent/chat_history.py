import logging
from collections import defaultdict
from itertools import zip_longest
from typing import Optional


class ChatHistory:
    def __init__(self, system_prompt: str = None, max_history_length: int = 10):
        self._history = defaultdict(list)
        self._system_prompt = system_prompt or str()
        self._max_history_len = max_history_length

    def update_sys_prompt(self, prompt: Optional[str]):
        if prompt:
            self._system_prompt = prompt

    def get_messages(self, username: str) -> list:
        messages = [{'role': 'system', 'content': self._system_prompt}]
        messages += self._history[username]

        logging.info(f"ChatHistory messages: \n"
                     f"{'\n'.join([f"{e['role']}: {e['content']}" for e in messages])}")
        return messages

    def add_user_message(self, username: str, message: str, system_prompt: str = None):
        self._history[username].append({'role': 'user', 'content': message})
        self.update_sys_prompt(system_prompt)
        self._update_history(username)

    def add_assistant_response(self, username: str, message: str, system_prompt: str = None):
        self._history[username].append({'role': 'assistant', 'content': message})
        self.update_sys_prompt(system_prompt)
        self._update_history(username)

    def _update_history(self, username: str):
        self._history[username] = self._history[username][-self._max_history_len:]
