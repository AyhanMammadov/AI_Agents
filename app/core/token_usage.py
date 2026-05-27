from contextvars import ContextVar
from copy import deepcopy


_TOKEN_USAGE = ContextVar("token_usage", default=None)


def reset_token_usage() -> None:
    _TOKEN_USAGE.set(
        {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "calls": [],
        }
    )


def _current() -> dict:
    usage = _TOKEN_USAGE.get()
    if usage is None:
        reset_token_usage()
        usage = _TOKEN_USAGE.get()
    return usage


def record_openai_usage(response, label: str, model: str) -> None:
    raw_usage = getattr(response, "usage", None)
    if raw_usage is None:
        return

    prompt_tokens = int(getattr(raw_usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(raw_usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(raw_usage, "total_tokens", 0) or 0)

    usage = _current()
    usage["prompt_tokens"] += prompt_tokens
    usage["completion_tokens"] += completion_tokens
    usage["total_tokens"] += total_tokens
    usage["calls"].append(
        {
            "label": label,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
    )


def get_token_usage() -> dict:
    return deepcopy(_current())
