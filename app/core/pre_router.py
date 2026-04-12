def detect_fast_intent(task: str) -> str | None:
    t = task.lower()

    # 1. простые вопросы (без LLM)
    if len(t) < 120:
        if any(q in t for q in ["кто", "что", "почему", "как", "объясни"]):
            return "simple_answer"

    # 2. business задачи
    if any(w in t for w in [
        "user story",
        "task",
        "tasks",
        "acceptance",
        "criteria",
        "разбей",
        "задач",
        "описание задачи",
    ]):
        return "business_task"

    # 3. build
    if any(w in t for w in [
        "сделай",
        "создай",
        "generate",
        "build",
        "app",
        "backend",
        "frontend",
        "fullstack",
        "telegram bot",
    ]):
        return "build_project"

    return None