import json
import os
import re
from datetime import datetime

from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.core.schemas import AgentName
from app.core.state_store import ProjectState
from app.core.executor import Executor, ExecutionError
from app.core.runtime import apply_generated_code
from app.core.auto_run import auto_run_project
from app.agents.registry import AGENT_REGISTRY
from app.prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)

# Always appended at the end of every pipeline (no LLM call, just contract checks)
_PIPELINE_TAIL = [AgentName.VALIDATOR, AgentName.DEPLOY]

# All valid agent name values
_AGENT_BY_NAME = {e.value: e for e in AgentName}


def _get_agent_pipeline(task: str) -> dict:
    """Ask LLM which agents to run and what project type."""
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"\n⚠️ ORCHESTRATOR LLM FAILED: {e} — using fallback pipeline")
        return {
            "project_type": "backend",
            "workflow": ["product_owner", "business_analyst", "architect", "senior_backend", "qa"],
        }


def _resolve_workflow(workflow: list) -> list:
    """Convert string agent names to AgentName enum instances, skip unknowns and tail agents."""
    tail_set = set(_PIPELINE_TAIL)
    resolved = []
    for name in workflow:
        agent = _AGENT_BY_NAME.get(name)
        if agent and agent not in tail_set and agent not in resolved:
            resolved.append(agent)
    return resolved + _PIPELINE_TAIL


def create_workspace(task: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", task.lower()).strip("_")
    safe_name = safe_name[:40] if safe_name else "project"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace = os.path.join("workspaces", f"{safe_name}_{timestamp}")
    os.makedirs(workspace, exist_ok=True)
    return workspace


def run_orchestrator(task: str) -> dict:
    workspace = create_workspace(task)
    state = ProjectState(task=task, workspace=workspace)

    orchestration = _get_agent_pipeline(task)
    state.project_type = orchestration.get("project_type", "backend")
    agent_sequence = _resolve_workflow(orchestration.get("workflow", []))

    print(f"\nPIPELINE: project_type={state.project_type}")
    print(f"Agents: {[a.value for a in agent_sequence]}")

    executor = Executor(AGENT_REGISTRY)
    pipeline_error = None

    try:
        for agent_name in agent_sequence:
            executor.run_agent(state, agent_name)

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
        "pipeline": [a.value for a in agent_sequence],
    }

    if pipeline_error:
        result["pipeline_error"] = pipeline_error

    return result
