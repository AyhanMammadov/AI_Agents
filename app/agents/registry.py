from app.core.schemas import AgentName, Artifact

from app.agents.product_owner import product_owner_agent
from app.agents.business_analyst import business_analyst_agent
from app.agents.architect import architect_agent
from app.agents.senior_backend import senior_backend_agent
from app.agents.senior_frontend import senior_frontend_agent
from app.agents.cx import cx_agent
from app.agents.ux_ui import ux_ui_agent
from app.agents.security import security_agent
from app.agents.qa import qa_agent
from app.agents.devops import devops_agent
from app.agents.code_reviewer import code_reviewer_agent


def build_agent_context(state, include_code: bool = False) -> dict:
    context = {
        "task": state.task,
        "project_type": state.project_type,
        "execution_mode": "normal",
    }

    # Pass accumulated knowledge artifacts in execution order
    for ref in ["brief", "spec", "architecture", "cx_review", "ux_ui_spec", "test_plan"]:
        if state.has_artifact(ref):
            context[ref] = state.get_artifact(ref).data

    # Code artifacts only for agents that need to read/review them
    if include_code:
        if state.has_artifact("backend_code"):
            context["backend_code"] = state.get_artifact("backend_code").data
        if state.has_artifact("frontend_code"):
            context["frontend_code"] = state.get_artifact("frontend_code").data

    if hasattr(state, "backend_retry_feedback") and state.backend_retry_feedback:
        context["execution_mode"] = "retry"
        context["backend_retry_feedback"] = state.backend_retry_feedback

    if hasattr(state, "frontend_retry_feedback") and state.frontend_retry_feedback:
        context["execution_mode"] = "retry"
        context["frontend_retry_feedback"] = state.frontend_retry_feedback

    return context


# ─── Planning & Analysis agents ───────────────────────────────────────────────

def planner_wrapper(state):
    result = product_owner_agent(build_agent_context(state))
    return Artifact(ref="brief", kind="task_brief", data=result)


def spec_wrapper(state):
    result = business_analyst_agent(build_agent_context(state))
    return Artifact(ref="spec", kind="spec", data=result)


def architect_wrapper(state):
    result = architect_agent(build_agent_context(state))
    return Artifact(ref="architecture", kind="architecture", data=result)


# ─── Experience agents ────────────────────────────────────────────────────────

def cx_wrapper(state):
    result = cx_agent(build_agent_context(state))
    return Artifact(ref="cx_review", kind="cx_review", data=result)


def ux_ui_wrapper(state):
    result = ux_ui_agent(build_agent_context(state))
    return Artifact(ref="ux_ui_spec", kind="ux_ui_spec", data=result)


# ─── Delivery agents ──────────────────────────────────────────────────────────

def backend_wrapper(state):
    from app.core.backend_contract import validate_backend_artifact

    result = senior_backend_agent(state)
    check = validate_backend_artifact(result)

    if not check["ok"]:
        print("\n❌ BACKEND CONTRACT FAILED")
        print(check["errors"])
        result = {
            "role": result.get("role", "senior_backend") if isinstance(result, dict) else "senior_backend",
            "deliverables": result.get("deliverables", {}) if isinstance(result, dict) else {},
            "files": result.get("files", []) if isinstance(result, dict) else [],
            "decisions": result.get("decisions", []) if isinstance(result, dict) else [],
            "assumptions": result.get("assumptions", []) if isinstance(result, dict) else [],
            "open_questions": result.get("open_questions", []) if isinstance(result, dict) else [],
            "error": result.get("error") if isinstance(result, dict) else "backend wrapper received invalid result",
            "contract_ok": False,
            "contract_errors": check["errors"],
        }
    else:
        print("\n✅ BACKEND CONTRACT OK")
        result["contract_ok"] = True
        result["contract_errors"] = []

    return Artifact(ref="backend_code", kind="backend_code", data=result)


def frontend_wrapper(state):
    from app.core.frontend_contract import validate_frontend_artifact

    context = build_agent_context(state, include_code=True)
    result = senior_frontend_agent(context)

    check = validate_frontend_artifact(result)

    if not check["ok"]:
        print("\n❌ FRONTEND CONTRACT FAILED")
        print(check["errors"])
        result = {
            "role": result.get("role", "senior_frontend") if isinstance(result, dict) else "senior_frontend",
            "deliverables": result.get("deliverables", {}) if isinstance(result, dict) else {},
            "files": result.get("files", []) if isinstance(result, dict) else [],
            "decisions": result.get("decisions", []) if isinstance(result, dict) else [],
            "assumptions": result.get("assumptions", []) if isinstance(result, dict) else [],
            "open_questions": result.get("open_questions", []) if isinstance(result, dict) else [],
            "error": result.get("error") if isinstance(result, dict) else "frontend wrapper received invalid result",
            "contract_ok": False,
            "contract_errors": check["errors"],
        }
    else:
        print("\n✅ FRONTEND CONTRACT OK")
        result["contract_ok"] = True
        result["contract_errors"] = []

    return Artifact(ref="frontend_code", kind="frontend_code", data=result)


# ─── Validation & hardening agents ────────────────────────────────────────────

def qa_wrapper(state):
    result = qa_agent(build_agent_context(state))
    return Artifact(ref="test_plan", kind="test_plan", data=result)


def security_wrapper(state):
    result = security_agent(build_agent_context(state, include_code=True))
    return Artifact(ref="security_review", kind="security_review", data=result)


def code_reviewer_wrapper(state):
    result = code_reviewer_agent(build_agent_context(state, include_code=True))
    return Artifact(ref="code_review", kind="code_review", data=result)


def devops_wrapper(state):
    result = devops_agent(build_agent_context(state, include_code=True))
    return Artifact(ref="devops_config", kind="devops_config", data=result)


# ─── Pipeline tail (no LLM calls) ─────────────────────────────────────────────

def validator_wrapper(state):
    checks_passed = []
    checks_failed = []
    errors = []

    if state.project_type in ["backend", "fullstack", "telegram_bot"]:
        if state.has_artifact("backend_code"):
            backend_data = state.get_artifact("backend_code").data
            if backend_data.get("contract_ok"):
                checks_passed.append("backend_contract")
            else:
                checks_failed.append("backend_contract")
                errors.extend(backend_data.get("contract_errors", []))
        else:
            checks_failed.append("backend_artifact_exists")
            errors.append("backend_code artifact missing")

    if state.project_type in ["frontend", "fullstack", "mobile_web_demo"]:
        if state.has_artifact("frontend_code"):
            frontend_data = state.get_artifact("frontend_code").data
            if frontend_data.get("contract_ok"):
                checks_passed.append("frontend_contract")
            else:
                checks_failed.append("frontend_contract")
                errors.extend(frontend_data.get("contract_errors", []))
        else:
            checks_failed.append("frontend_artifact_exists")
            errors.append("frontend_code artifact missing")

    return Artifact(
        ref="validation_result",
        kind="validation_result",
        data={
            "ok": len(errors) == 0,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "errors": errors,
        },
    )


def deploy_wrapper(state):
    validation_data = {}
    if state.has_artifact("validation_result"):
        validation_data = state.get_artifact("validation_result").data

    return Artifact(
        ref="deploy_result",
        kind="deploy_result",
        data={
            "ok": validation_data.get("ok", False),
            "url": None,
            "logs": [],
            "errors": validation_data.get("errors", []),
            "message": "deploy stub — not yet implemented",
        },
    )


AGENT_REGISTRY = {
    AgentName.PLANNER: planner_wrapper,
    AgentName.SPEC: spec_wrapper,
    AgentName.ARCHITECT: architect_wrapper,
    AgentName.CX: cx_wrapper,
    AgentName.UX_UI: ux_ui_wrapper,
    AgentName.BACKEND: backend_wrapper,
    AgentName.FRONTEND: frontend_wrapper,
    AgentName.SECURITY: security_wrapper,
    AgentName.QA: qa_wrapper,
    AgentName.CODE_REVIEWER: code_reviewer_wrapper,
    AgentName.DEVOPS: devops_wrapper,
    AgentName.VALIDATOR: validator_wrapper,
    AgentName.DEPLOY: deploy_wrapper,
}
