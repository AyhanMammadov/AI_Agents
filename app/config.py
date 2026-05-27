import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_RUN_TOKEN = os.getenv("API_RUN_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

CHEAP_MODEL = os.getenv("CHEAP_MODEL", "gpt-4o-mini")
CHAT_MODEL = os.getenv("CHAT_MODEL", CHEAP_MODEL)
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")

STRONG_MODEL = os.getenv("STRONG_MODEL", "gpt-4.1")

ORCHESTRATOR_MODE = os.getenv("ORCHESTRATOR_MODE", "fast").lower()
RAILWAY_DEPLOY_ENABLED = os.getenv("RAILWAY_DEPLOY_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}
RAILWAY_SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "")
RAILWAY_PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_URL", "")


def _parse_int_set(value: str) -> set[int]:
    result: set[int] = set()
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            continue
    return result


ALLOWED_TELEGRAM_USER_IDS = _parse_int_set(os.getenv("ALLOWED_TELEGRAM_USER_IDS", ""))


def is_telegram_user_allowed(user_id: int | None) -> bool:
    if not ALLOWED_TELEGRAM_USER_IDS:
        return True
    return user_id in ALLOWED_TELEGRAM_USER_IDS
