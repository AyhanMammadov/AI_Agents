import re

from app.core.schemas import (
    ProjectType,
    AgentName,
    AgentTask,
    RoutePlan,
)


def contains_phrase(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def contains_token(text: str, tokens: list[str]) -> bool:
    words = set(re.findall(r"[a-zA-Z0-9_./+-]+", text))
    return any(token in words for token in tokens)


def build_route_plan(task: str) -> RoutePlan:
    task_lower = task.lower()

    # =========================
    # DEFINE PROJECT TYPE SIGNALS
    # =========================
    mobile_phrases = [
        "react native", "mobile app",
    ]
    mobile_tokens = [
        "mobile", "expo", "flutter", "android", "ios", "apk",
    ]

    backend_phrases = [
        "fastapi", "backend service",
    ]
    backend_tokens = [
        "backend", "api", "server", "auth", "database", "endpoint", "service",
    ]

    frontend_phrases = [
        "frontend", "dashboard", "react", "vite",
    ]
    frontend_tokens = [
        "ui", "web", "page", "form", "screen",
    ]

    is_mobile = contains_phrase(task_lower, mobile_phrases) or contains_token(task_lower, mobile_tokens)
    is_backend = contains_phrase(task_lower, backend_phrases) or contains_token(task_lower, backend_tokens)
    is_frontend = contains_phrase(task_lower, frontend_phrases) or contains_token(task_lower, frontend_tokens)

    is_fullstack_explicit = "fullstack" in task_lower
    is_telegram_bot = "telegram" in task_lower and "bot" in task_lower

    # =========================
    # CHOOSE PROJECT TYPE
    # =========================
    if is_mobile and "flutter" in task_lower:
        project_type = ProjectType.MOBILE_FLUTTER
    elif is_mobile:
        project_type = ProjectType.MOBILE_EXPO
    elif is_telegram_bot:
        project_type = ProjectType.TELEGRAM_BOT
    elif is_fullstack_explicit:
        project_type = ProjectType.FULLSTACK
    elif is_backend and is_frontend:
        project_type = ProjectType.FULLSTACK
    elif is_backend:
        project_type = ProjectType.BACKEND
    elif is_frontend:
        project_type = ProjectType.FRONTEND
    else:
        project_type = ProjectType.BACKEND

    # =========================
    # FLAGS
    # =========================
    needs_frontend = project_type in [
        ProjectType.FRONTEND,
        ProjectType.FULLSTACK,
    ]

    needs_backend = project_type in [
        ProjectType.BACKEND,
        ProjectType.FULLSTACK,
        ProjectType.TELEGRAM_BOT,
    ]

    needs_mobile = project_type in [
        ProjectType.MOBILE_EXPO,
        ProjectType.MOBILE_FLUTTER,
    ]

    # =========================
    # TASKS PIPELINE
    # =========================
    tasks = [
        AgentTask(
            agent=AgentName.PLANNER,
            goal="Convert raw task into structured brief",
            input_refs=[],
            output_ref="brief",
        ),
        AgentTask(
            agent=AgentName.SPEC,
            goal="Create structured product and execution spec",
            input_refs=["brief"],
            output_ref="spec",
        ),
        AgentTask(
            agent=AgentName.ARCHITECT,
            goal="Create architecture and file plan",
            input_refs=["brief", "spec"],
            output_ref="architecture",
        ),
    ]

    if needs_backend:
        tasks.append(
            AgentTask(
                agent=AgentName.BACKEND,
                goal="Generate backend code",
                input_refs=["spec", "architecture"],
                output_ref="backend_code",
            )
        )

    if needs_frontend:
        tasks.append(
            AgentTask(
                agent=AgentName.FRONTEND,
                goal="Generate frontend code",
                input_refs=["spec", "architecture"],
                output_ref="frontend_code",
            )
        )

    if needs_mobile:
        tasks.append(
            AgentTask(
                agent=AgentName.MOBILE,
                goal="Generate mobile app code",
                input_refs=["spec", "architecture"],
                output_ref="mobile_code",
            )
        )

    tasks.extend([
        AgentTask(
            agent=AgentName.QA,
            goal="Create validation checks",
            input_refs=["spec", "architecture"],
            output_ref="test_plan",
        ),
        AgentTask(
            agent=AgentName.VALIDATOR,
            goal="Validate build and runtime",
            input_refs=["test_plan"],
            output_ref="validation_result",
        ),
        AgentTask(
            agent=AgentName.DEPLOY,
            goal="Deploy runnable app and return result",
            input_refs=["validation_result"],
            output_ref="deploy_result",
        ),
    ])

    return RoutePlan(
        project_type=project_type,
        needs_frontend=needs_frontend,
        needs_backend=needs_backend,
        needs_mobile=needs_mobile,
        tasks=tasks,
    )