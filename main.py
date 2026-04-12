import os
import datetime
from typing import Any

from app.core.router import build_route_plan
from app.core.state_store import ProjectState
from app.core.executor import Executor, ExecutionError
from app.agents.registry import AGENT_REGISTRY
from app.agents.intent_router import ai_intent_router
from app.core.runtime import apply_generated_code
from app.core.auto_run import auto_run_project


def create_workspace(task: str) -> str:
    safe_name = task.replace(" ", "_")[:30]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"workspaces/{safe_name}_{timestamp}"
    os.makedirs(path, exist_ok=True)
    return path


def print_user_result(run_result: dict[str, Any]) -> None:
    print("\n🌐 RESULT FOR USER:")

    if not isinstance(run_result, dict):
        print("Run result is invalid")
        return

    frontend = run_result.get("frontend") or {}
    backend = run_result.get("backend") or {}
    health = run_result.get("health") or {}
    errors = run_result.get("errors") or []

    if frontend.get("url"):
        print(f"Frontend: {frontend['url']}")

    if backend.get("url"):
        print(f"Backend: {backend['url']}")

    if backend.get("health_url"):
        print(f"Health URL: {backend['health_url']}")

    if backend and not backend.get("ok"):
        print("Backend start: FAILED")
        if backend.get("stderr_log"):
            print(f"Backend stderr log: {backend['stderr_log']}")
        if backend.get("stdout_log"):
            print(f"Backend stdout log: {backend['stdout_log']}")

    if health.get("ok") is True:
        print("Health: OK")
    elif health:
        print("Health: FAILED")

    if errors:
        print("Errors:")
        for err in errors:
            print(f"- {err}")


def run_system(task: str) -> dict[str, Any]:
    task = task.strip()

    if not task:
        return {
            "ok": False,
            "error": "Пустая задача",
        }

    print("\n🚀 START SYSTEM")
    print(f"Task: {task}")

    intent_result = ai_intent_router(task)

    print("\n🧠 INTENT ROUTER:")
    print(intent_result)

    if intent_result.get("error"):
        print("\n⚠️ INTENT ROUTER FAILED")
        print(intent_result.get("error"))
        print("По умолчанию продолжаем как build_project")

    elif intent_result.get("intent") != "build_project":
        print("\n⛔ BUILD PIPELINE NOT STARTED")
        print(f"Detected intent: {intent_result.get('intent')}")
        print(f"Reason: {intent_result.get('reason')}")
        print(f"Confidence: {intent_result.get('confidence')}")
        return {
            "ok": True,
            "intent_only": True,
            "intent": intent_result.get("intent"),
            "reason": intent_result.get("reason"),
            "confidence": intent_result.get("confidence"),
        }

    workspace = create_workspace(task)

    state = ProjectState(
        task=task,
        workspace=workspace,
    )

    route = build_route_plan(task)
    state.project_type = route.project_type.value

    print(f"\n📊 PROJECT TYPE: {state.project_type}")
    print("🧭 WORKFLOW:", [step.agent.value for step in route.tasks])

    executor = Executor(AGENT_REGISTRY)
    pipeline_error = None

    try:
        for step in route.tasks:
            executor.run_agent(state, step.agent)

        apply_generated_code(state)

        run_result = auto_run_project(state)
        state.auto_run_result = run_result

        print("\n🚀 AUTO RUN RESULT:")
        print(run_result)

        print_user_result(run_result)

    except ExecutionError as e:
        pipeline_error = str(e)
        print(f"\n⛔ PIPELINE STOPPED: {pipeline_error}")

    except Exception as e:
        pipeline_error = f"Unexpected error: {str(e)}"
        print(f"\n💥 UNEXPECTED ERROR: {pipeline_error}")

    snapshot = state.snapshot()

    if pipeline_error:
        snapshot["ok"] = False
        snapshot["pipeline_error"] = pipeline_error
    else:
        snapshot["ok"] = True

    print("\n🎯 FINAL STATE:")
    print(snapshot)

    return snapshot


if __name__ == "__main__":
    user_task = input("Напиши задачу: ").strip()

    if not user_task:
        print("Пустая задача")
    else:
        result = run_system(user_task)
        print("\nFINAL RESULT:\n")
        print(result)