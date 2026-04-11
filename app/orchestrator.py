from openai import OpenAI
import json
import os
import datetime
import re
from typing import Any

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from app.project_memory import create_project_memory, update_memory

from app.agents.product_owner import product_owner_agent
from app.agents.business_analyst import business_analyst_agent
from app.agents.architect import architect_agent
from app.agents.senior_backend import senior_backend_agent
from app.agents.senior_frontend import senior_frontend_agent
from app.agents.qa import qa_agent
from app.agents.cx import cx_agent
from app.agents.ux_ui import ux_ui_agent
from app.agents.security import security_agent
from app.agents.devops import devops_agent
from app.agents.code_reviewer import code_reviewer_agent
from app.deploy_agent import deploy_agent

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_project_name(task: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", task.lower()).strip("_")[:40]
    if not slug:
        slug = "project"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{slug}_{timestamp}"


def create_workspace(task: str) -> str:
    base_dir = "workspaces"
    os.makedirs(base_dir, exist_ok=True)

    project_name = generate_project_name(task)
    project_path = os.path.join(base_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    return project_path


def save_generated_files(files: list[dict[str, Any]], workspace: str) -> list[str]:
    saved_paths: list[str] = []

    for file in files:
        path = file.get("path")
        content = file.get("content", "")

        if not path or not isinstance(path, str):
            continue

        full_path = os.path.join(workspace, path)

        folder = os.path.dirname(full_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        saved_paths.append(full_path)

    return saved_paths


def call_orchestrator_llm(task: str) -> dict[str, Any]:
    fallback = {
        "task_type": "feature",
        "workflow": [
            "product_owner",
            "business_analyst",
            "architect",
            "cx",
            "ux_ui",
            "security",
            "senior_backend",
            "senior_frontend",
            "qa",
            "devops",
            "code_reviewer",
        ],
        "reason": "fallback used",
    }

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

        content = response.choices[0].message.content
        if not content:
            fallback["reason"] = "empty orchestrator response, fallback used"
            return fallback

        decision = json.loads(content)
        return decision

    except Exception as e:
        fallback["reason"] = f"orchestrator failed, fallback used: {str(e)}"
        return fallback


def normalize_workflow(workflow: list[Any]) -> list[str]:
    allowed_agents = [
        "product_owner",
        "business_analyst",
        "architect",
        "cx",
        "ux_ui",
        "security",
        "senior_backend",
        "senior_frontend",
        "qa",
        "devops",
        "code_reviewer",
    ]

    normalized: list[str] = []

    for agent in workflow:
        if isinstance(agent, str) and agent in allowed_agents and agent not in normalized:
            normalized.append(agent)

    if not normalized:
        return [
            "product_owner",
            "business_analyst",
            "architect",
            "cx",
            "ux_ui",
            "security",
            "senior_backend",
            "senior_frontend",
            "qa",
            "devops",
            "code_reviewer",
        ]

    return normalized


def build_context(task: str, memory: dict[str, Any], workspace: str) -> dict[str, Any]:
    return {
        "task": task,
        "workspace": workspace,
        "decisions": memory["decisions"],
        "constraints": memory["constraints"],
        "assumptions": memory["assumptions"],
        "open_questions": memory["open_questions"],
        "artifacts": memory["artifacts"],
    }


def run_orchestrator(task: str) -> dict[str, Any]:
    workspace = create_workspace(task)
    print(f"\nPROJECT WORKSPACE: {workspace}\n")

    memory = create_project_memory(task)

    decision = call_orchestrator_llm(task)
    requested_workflow = normalize_workflow(decision.get("workflow", []))
    task_type = decision.get("task_type", "unknown")
    reason = decision.get("reason", "")

    print("TASK TYPE:", task_type)
    print("WORKFLOW:", requested_workflow)
    if reason:
        print("REASON:", reason)
    print()

    results: dict[str, Any] = {"task": task}
    saved_files: list[str] = []
    errors: list[str] = []

    analysis_agents = ["product_owner", "business_analyst", "architect"]
    delivery_agents = [
        "cx",
        "ux_ui",
        "security",
        "senior_backend",
        "senior_frontend",
        "qa",
        "devops",
        "code_reviewer",
    ]

    # -------------------------
    # STAGE 1: ANALYSIS
    # -------------------------
    for agent in analysis_agents:
        if agent not in requested_workflow:
            continue

        try:
            print(f"➡️ RUNNING: {agent}")
            context = build_context(task, memory, workspace)

            if agent == "product_owner":
                result = product_owner_agent(context)
                results["product_owner"] = result

            elif agent == "business_analyst":
                result = business_analyst_agent(context)
                results["business_analyst"] = result

            elif agent == "architect":
                result = architect_agent(context)
                results["architect"] = result

            else:
                continue

            memory = update_memory(memory, result)

        except Exception as e:
            error_message = f"{agent} failed: {str(e)}"
            print(error_message)
            errors.append(error_message)

    # -------------------------
    # STAGE 2: DELIVERY
    # -------------------------
    for agent in delivery_agents:
        if agent not in requested_workflow:
            continue

        try:
            print(f"➡️ RUNNING: {agent}")
            context = build_context(task, memory, workspace)

            if agent == "cx":
                result = cx_agent(context)
                results["cx"] = result

            elif agent == "ux_ui":
                result = ux_ui_agent(context)
                results["ux_ui"] = result

            elif agent == "security":
                result = security_agent(context)
                results["security"] = result

            elif agent == "senior_backend":
                result = senior_backend_agent(context)
                results["backend"] = result

                if isinstance(result, dict) and "files" in result:
                    saved = save_generated_files(result["files"], workspace)
                    saved_files.extend(saved)

            elif agent == "senior_frontend":
                result = senior_frontend_agent(context)
                results["frontend"] = result

                if isinstance(result, dict) and "files" in result:
                    saved = save_generated_files(result["files"], workspace)
                    saved_files.extend(saved)

            elif agent == "qa":
                result = qa_agent(context)
                results["qa"] = result

            elif agent == "devops":
                result = devops_agent(context)
                results["devops"] = result

            elif agent == "code_reviewer":
                result = code_reviewer_agent(context)
                results["code_reviewer"] = result

            else:
                continue

            memory = update_memory(memory, result)

        except Exception as e:
            error_message = f"{agent} failed: {str(e)}"
            print(error_message)
            errors.append(error_message)

    # -------------------------
    # STAGE 3: DEPLOY CHECK
    # -------------------------
    try:
        print("➡️ RUNNING: deploy")

        deploy_result = deploy_agent(
            {
                "workspace": workspace,
                "artifacts": memory["artifacts"],
                "decisions": memory["decisions"],
                "constraints": memory["constraints"],
            }
        )

        results["deploy"] = deploy_result
        memory = update_memory(memory, deploy_result)

    except Exception as e:
        error_message = f"deploy failed: {str(e)}"
        print(error_message)
        errors.append(error_message)

    print("\n✅ DONE\n")

    return {
        "workspace": workspace,
        "files": saved_files,
        "workflow": requested_workflow,
        "task_type": task_type,
        "reason": reason,
        "errors": errors,
        "memory": memory,
        "results": results,
    }