import os
import re
from datetime import datetime

from app.core.router import build_route_plan
from app.core.state_store import ProjectState
from app.core.executor import Executor
from app.core.runtime import apply_generated_code
from app.agents.registry import AGENT_REGISTRY


def create_workspace(task: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", task.lower()).strip("_")
    safe_name = safe_name[:40] if safe_name else "project"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace = os.path.join("workspaces", f"{safe_name}_{timestamp}")

    os.makedirs(workspace, exist_ok=True)
    return workspace


def run_orchestrator(task: str) -> dict:
    # 1. create workspace
    workspace = create_workspace(task)

    # 2. create state
    state = ProjectState(
        task=task,
        workspace=workspace,
    )

    # 3. build route plan
    route_plan = build_route_plan(task)
    state.project_type = route_plan.project_type.value

    # 4. create executor
    executor = Executor(AGENT_REGISTRY)

    # 5. run all planned agents
    for agent_task in route_plan.tasks:
        executor.run_agent(state, agent_task.agent)

    # 6. write generated code to workspace
    apply_generated_code(state)

    # 7. return result
    return {
        "task": state.task,
        "project_type": state.project_type,
        "workspace": state.workspace,
        "artifacts": list(state.artifacts.keys()),
        "history": state.run_history,
        "snapshot": state.snapshot(),
    }