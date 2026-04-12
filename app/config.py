import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1")
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")

CHEAP_MODEL = "gpt-4o-mini"
STRONG_MODEL = "gpt-4.1"