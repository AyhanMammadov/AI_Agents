def detect_fast_intent(task: str) -> str | None:
    t = task.lower().strip()

    # status request — check first, high confidence patterns
    if any(w in t for w in [
        "статус", "что уже готово", "что готово", "где файл", "где проект",
        "где workspace", "какой workspace", "последний проект", "последний результат",
        "status", "what's done", "what is done",
    ]):
        return "status_request"

    # business task structuring — explicit keywords
    if any(w in t for w in [
        "user story", "acceptance criteria", "acceptance criteria",
        "разбей на задачи", "декомпозиция", "task breakdown",
        "опиши задачу", "описание задачи для команды",
    ]):
        return "business_task"

    # build project — strong explicit signals only
    if any(w in t for w in [
        "создай проект", "сделай проект", "напиши проект",
        "создай приложение", "сделай приложение",
        "создай backend", "сделай backend",
        "создай frontend", "сделай frontend",
        "create a project", "build a project",
        "create an app", "build an app",
        "create a backend", "build a backend",
        "create a frontend", "build a frontend",
        "telegram bot", "телеграм бот",
        "fullstack", "full-stack",
        "generate code", "generate a",
    ]):
        return "build_project"

    # simple answer — short question with question words
    if len(t) < 150:
        question_words_ru = ["кто ", "что ", "почему ", "зачем ", "как ", "объясни ", "расскажи "]
        question_words_en = ["what ", "why ", "how ", "who ", "explain ", "what's ", "whats "]
        if any(t.startswith(q) or f" {q}" in t for q in question_words_ru + question_words_en):
            if not any(w in t for w in ["сделай", "создай", "напиши", "build", "create", "make", "generate"]):
                return "simple_answer"

    return None
