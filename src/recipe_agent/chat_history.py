import logging
import re
from collections import defaultdict
from typing import Optional

MAX_USERS = 24


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
                     f"{'\n'.join([f"{e['role']}: {e['content']}" for e in messages if e['role'] != 'system'])}")
        return messages

    def get_last_message_with_url(self, username: str) -> Optional[list]:
        for message in reversed(self._history[username]):
            if message['role'] != 'user':
                continue
            urls = re.findall(r'https?://\S+', message['content'])
            if urls:
                return urls

        return None

    def add_user_message(self, username: str, message: str, system_prompt: str = None):
        self._history[username].append({'role': 'user', 'content': message})
        self.update_sys_prompt(system_prompt)
        self._update_history(username)

    def add_assistant_response(self, username: str, message: str, system_prompt: str = None):
        self._history[username].append({'role': 'assistant', 'content': message})
        self.update_sys_prompt(system_prompt)
        self._update_history(username)

    def _check_history_size(self, username: str):
        if len(self._history) > MAX_USERS:
            diff = len(self._history) - MAX_USERS
            for idx, key in enumerate(self._history):
                if key == username:
                    continue
                self._history.pop(key)
                if idx >= diff:
                    break

    def _update_history(self, username: str):
        self._check_history_size(username)
        self._history[username] = self._history[username][-self._max_history_len:]
