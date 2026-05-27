import json
import os
import re
from datetime import datetime

from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL, ORCHESTRATOR_MODE
from app.core.schemas import AgentName
from app.core.router import build_route_plan
from app.core.state_store import ProjectState
from app.core.executor import Executor, ExecutionError
from app.core.runtime import apply_generated_code
from app.core.auto_run import auto_run_project
from app.core.token_usage import record_openai_usage
from app.agents.registry import AGENT_REGISTRY
from app.prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

client = OpenAI(api_key=OPENAI_API_KEY)

# Validator checks contracts (no LLM). Deploy happens after code is written — see below.
_PIPELINE_TAIL = [AgentName.VALIDATOR]

# All valid agent name values
_AGENT_BY_NAME = {e.value: e for e in AgentName}


def _get_agent_pipeline(task: str) -> dict:
    """Ask LLM which agents to run and what project type."""
    fast_pipeline = _get_fast_agent_pipeline(task)
    if fast_pipeline["project_type"] == "mobile_web_demo":
        return fast_pipeline

    if ORCHESTRATOR_MODE != "llm" or not OPENAI_API_KEY:
        return fast_pipeline

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
        record_openai_usage(response, "orchestrator", CHAT_MODEL)
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"\n⚠️ ORCHESTRATOR LLM FAILED: {e} — using fallback pipeline")
        return _get_fast_agent_pipeline(task)


def _needs_security_review(task: str) -> bool:
    task_lower = task.lower()
    return any(
        marker in task_lower
        for marker in [
            "auth",
            "login",
            "password",
            "payment",
            "token",
            "oauth",
            "jwt",
            "lichn",
            "parol",
            "oplata",
        ]
    )


def _get_fast_agent_pipeline(task: str) -> dict:
    """Token-saving deterministic orchestration for common project requests."""

    route = build_route_plan(task)
    project_type = route.project_type.value

    if project_type == "mobile_web_demo":
        return {
            "project_type": project_type,
            "task_type": "frontend_only",
            "workflow": [
                AgentName.PLANNER.value,
                AgentName.UX_UI.value,
                AgentName.FRONTEND.value,
            ],
            "reason": "mobile web demo uses a lean product -> ux -> frontend pipeline to save tokens",
        }

    workflow: list[str] = []
    for item in route.tasks:
        if item.agent in {AgentName.VALIDATOR, AgentName.DEPLOY, AgentName.MOBILE}:
            continue
        if item.agent == AgentName.FRONTEND:
            if AgentName.UX_UI.value not in workflow:
                workflow.append(AgentName.UX_UI.value)
        if item.agent.value not in workflow:
            workflow.append(item.agent.value)

    if _needs_security_review(task) and AgentName.SECURITY.value not in workflow:
        if AgentName.QA.value in workflow:
            workflow.insert(workflow.index(AgentName.QA.value) + 1, AgentName.SECURITY.value)
        else:
            workflow.append(AgentName.SECURITY.value)

    return {
        "project_type": project_type,
        "task_type": "feature",
        "workflow": workflow,
        "reason": "fast deterministic routing selected to save tokens",
    }


def _resolve_workflow(workflow: list) -> list:
    """Convert string agent names to AgentName enum instances, skip unknowns and tail agents."""
    tail_set = set(_PIPELINE_TAIL)
    unsupported = {AgentName.MOBILE, AgentName.FIX}
    resolved = []
    for name in workflow:
        agent = _AGENT_BY_NAME.get(name)
        if agent and agent not in tail_set and agent not in unsupported and agent not in resolved:
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

        # Deploy = actually start the project (after code is on disk)
        print("\n🚀 DEPLOYING...")
        run_result = auto_run_project(state)
        state.auto_run_result = run_result

        if run_result.get("ok"):
            backend_url = (run_result.get("backend") or {}).get("url")
            frontend_url = (run_result.get("frontend") or {}).get("url")
            print(f"✅ DEPLOY OK — backend={backend_url} frontend={frontend_url}")
        else:
            print(f"⚠️ DEPLOY ISSUES: {run_result.get('errors', [])}")

    except ExecutionError as e:
        pipeline_error = str(e)
    except Exception as e:
        pipeline_error = f"Unexpected error: {str(e)}"

    auto_run = getattr(state, "auto_run_result", None) or {}
    result = {
        "ok": pipeline_error is None,
        "task": state.task,
        "project_type": state.project_type,
        "workspace": state.workspace,
        "artifacts": list(state.artifacts.keys()),
        "history": state.run_history,
        "snapshot": state.snapshot(),
        "auto_run_result": auto_run,
        "pipeline": [a.value for a in agent_sequence],
        "deploy": {
            "ok": auto_run.get("ok", False),
            "backend_url": (auto_run.get("backend") or {}).get("url"),
            "frontend_url": (auto_run.get("frontend") or {}).get("url"),
            "railway_url": (auto_run.get("railway") or {}).get("public_url"),
            "health_url": (auto_run.get("health") or {}).get("body") and (auto_run.get("backend") or {}).get("health_url"),
            "errors": auto_run.get("errors", []),
        },
    }

    if pipeline_error:
        result["pipeline_error"] = pipeline_error

    return result
