import re


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _has_token(text: str, tokens: list[str]) -> bool:
    words = set(re.findall(r"[\w./+-]+", text, flags=re.UNICODE))
    return any(token in words for token in tokens)


def detect_fast_intent(task: str) -> str | None:
    """Cheap deterministic routing before any LLM call."""

    t = task.lower().strip()
    if not t:
        return None

    build_words = [
        "create",
        "build",
        "make",
        "generate",
        "scaffold",
        "создай",
        "сделай",
        "напиши",
        "собери",
        "сгенерируй",
        "разработай",
        "sozday",
        "sdelai",
        "sdelay",
        "napishi",
        "sobery",
        "sgeneriruy",
    ]
    project_words = [
        "project",
        "app",
        "application",
        "website",
        "frontend",
        "backend",
        "fullstack",
        "mobile",
        "bot",
        "api",
        "dashboard",
        "проект",
        "приложение",
        "мобильное",
        "мобильный",
        "мобильноe",
        "сайт",
        "бот",
        "интерфейс",
        "демо",
        "prilojenie",
        "prilozhenie",
        "proekt",
        "sayt",
        "sait",
    ]

    if _has_any(t, ["status", "статус", "что готово", "что уже готово", "где проект", "где файл"]):
        return "status_request"

    if _has_any(t, ["fix", "bug", "crash", "traceback", "exception", "почини", "исправ", "ошибк"]):
        return "fix_project"

    if _has_any(t, ["change project", "edit project", "add feature", "добав", "измени", "доработ"]):
        return "edit_project"

    if _has_any(t, ["user story", "acceptance criteria", "task breakdown", "разбей", "декомпоз"]):
        return "business_task"

    if _has_any(t, ["analyze", "analyse", "проанализ", "review this", "explain", "объясни", "расскажи"]):
        if not (_has_token(t, build_words) and _has_any(t, project_words)):
            return "simple_answer"

    if _has_token(t, build_words) and _has_any(t, project_words):
        return "build_project"

    if _has_any(t, ["telegram bot", "телеграм бот", "fullstack", "full-stack", "mobile app", "мобильное приложение", "web demo"]):
        return "build_project"

    question_starts = [
        "what ",
        "why ",
        "how ",
        "who ",
        "что ",
        "почему ",
        "зачем ",
        "как ",
        "kak ",
        "chto ",
        "pochemu ",
        "zachem ",
    ]
    if len(t) < 220 and any(t.startswith(prefix) for prefix in question_starts):
        return "simple_answer"

    return None
