import json
from typing import Any

from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.agents.intent_router import ai_intent_router
from app.core.pre_router import detect_fast_intent
from app.orchestrator import run_orchestrator
from app.core.session_store import save_last_result, get_last_result

client = OpenAI(api_key=OPENAI_API_KEY)


def _chat_answer(system_prompt: str, user_text: str) -> str:
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()


def handle_simple_answer(task: str) -> dict[str, Any]:
    answer = _chat_answer(
        system_prompt=(
            "Ты полезный AI ассистент. "
            "Отвечай коротко, понятно и без воды."
        ),
        user_text=task,
    )
    return {
        "ok": True,
        "mode": "simple_answer",
        "answer": answer,
    }


def handle_business_task(task: str) -> dict[str, Any]:
    answer = _chat_answer(
        system_prompt=(
            "Ты senior product manager и business analyst. "
            "Верни результат на русском языке в формате:\n"
            "1. Краткое понимание\n"
            "2. User Story\n"
            "3. Acceptance Criteria\n"
            "4. Tasks\n"
            "5. Task Description\n"
            "Пиши чётко и без воды."
        ),
        user_text=task,
    )
    return {
        "ok": True,
        "mode": "business_task",
        "answer": answer,
    }


def handle_build_project(task: str) -> dict[str, Any]:
    result = run_orchestrator(task)
    result["mode"] = "build_project"
    save_last_result(result)
    return result


def handle_status_request() -> dict[str, Any]:
    last_result = get_last_result()

    if not last_result:
        return {
            "ok": False,
            "mode": "status_request",
            "error": "Пока нет последнего проекта или результата.",
        }

    return {
        "ok": True,
        "mode": "status_request",
        "task": last_result.get("task"),
        "project_type": last_result.get("project_type"),
        "workspace": last_result.get("workspace"),
        "artifacts": last_result.get("artifacts"),
        "history": last_result.get("history"),
        "auto_run_result": last_result.get("auto_run_result"),
        "pipeline_error": last_result.get("pipeline_error"),
    }


def run_system(task: str) -> dict[str, Any]:
    task = task.strip()

    if not task:
        return {
            "ok": False,
            "error": "Пустая задача",
        }

    print("\nSTART SYSTEM")
    print(f"Task: {task}")

    fast_intent = detect_fast_intent(task)
    if fast_intent:
        intent_result = {"intent": fast_intent}
        print(f"\nINTENT ROUTER (fast): {fast_intent}")
    else:
        intent_result = ai_intent_router(task)
        print("\nINTENT ROUTER (llm):")
        print(intent_result)

    if intent_result.get("error"):
        return {
            "ok": False,
            "error": intent_result.get("error"),
            "mode": "routing_failed",
        }

    mode = intent_result.get("intent")

    if mode == "simple_answer":
        print("\nMODE: SIMPLE ANSWER")
        return handle_simple_answer(task)

    if mode == "business_task":
        print("\nMODE: BUSINESS TASK")
        return handle_business_task(task)

    if mode == "build_project":
        print("\nMODE: BUILD PROJECT")
        return handle_build_project(task)

    if mode == "status_request":
        print("\nMODE: STATUS REQUEST")
        return handle_status_request()

    if mode == "edit_project":
        return {
            "ok": False,
            "mode": "edit_project",
            "error": "Режим edit_project ещё не подключён",
        }

    if mode == "fix_project":
        return {
            "ok": False,
            "mode": "fix_project",
            "error": "Режим fix_project ещё не подключён",
        }

    return {
        "ok": False,
        "error": f"Неизвестный intent: {mode}",
        "intent_result": intent_result,
    }


if __name__ == "__main__":
    user_task = input("Напиши задачу: ").strip()

    if not user_task:
        print("Пустая задача")
    else:
        result = run_system(user_task)
        print("\nFINAL RESULT:\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))