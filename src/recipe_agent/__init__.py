import logging

from dotenv import load_dotenv

load_dotenv()

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore.connection").setLevel(logging.ERROR)
logging.getLogger("httpcore.http11").setLevel(logging.ERROR)
logging.getLogger("aiosqlite").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)
# logging.getLogger("httpcore.http11").setLevel(logging.ERROR)
# logging.getLogger("httpcore.http11").setLevel(logging.ERROR)
