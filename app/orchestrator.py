import os
import re
from datetime import datetime

from app.core.router import build_route_plan
from app.core.state_store import ProjectState
from app.core.executor import Executor, ExecutionError
from app.core.runtime import apply_generated_code
from app.core.auto_run import auto_run_project
from app.agents.registry import AGENT_REGISTRY


def create_workspace(task: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", task.lower()).strip("_")
    safe_name = safe_name[:40] if safe_name else "project"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace = os.path.join("workspaces", f"{safe_name}_{timestamp}")

    os.makedirs(workspace, exist_ok=True)
    return workspace


def run_orchestrator(task: str) -> dict:
    workspace = create_workspace(task)

    state = ProjectState(
        task=task,
        workspace=workspace,
    )

    route_plan = build_route_plan(task)
    state.project_type = route_plan.project_type.value

    executor = Executor(AGENT_REGISTRY)
    pipeline_error = None

    try:
        for agent_task in route_plan.tasks:
            executor.run_agent(state, agent_task.agent)

        apply_generated_code(state)

        run_result = auto_run_project(state)
        state.auto_run_result = run_result

    except ExecutionError as e:
        pipeline_error = str(e)

    except Exception as e:
        pipeline_error = f"Unexpected error: {str(e)}"

    result = {
        "ok": pipeline_error is None,
        "task": state.task,
        "project_type": state.project_type,
        "workspace": state.workspace,
        "artifacts": list(state.artifacts.keys()),
        "history": state.run_history,
        "snapshot": state.snapshot(),
        "auto_run_result": getattr(state, "auto_run_result", None),
    }

    if pipeline_error:
        result["pipeline_error"] = pipeline_error

    return result