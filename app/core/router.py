import re

from app.core.schemas import AgentName, AgentTask, ProjectType, RoutePlan


def contains_phrase(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def contains_token(text: str, tokens: list[str]) -> bool:
    words = set(re.findall(r"[\w./+-]+", text, flags=re.UNICODE))
    return any(token in words for token in tokens)


def build_route_plan(task: str) -> RoutePlan:
    task_lower = task.lower()

    mobile_phrases = [
        "react native",
        "mobile app",
        "мобильное приложение",
        "мобильный app",
        "мобильное демо",
        "демо приложение",
    ]
    mobile_tokens = [
        "mobile",
        "expo",
        "flutter",
        "android",
        "ios",
        "apk",
        "мобильное",
        "мобильный",
        "мобилка",
        "демо",
    ]

    backend_phrases = [
        "fastapi",
        "backend service",
        "rest api",
        "crud app",
        "crud api",
        "бэкенд",
        "бекенд",
        "серверная часть",
    ]
    backend_tokens = [
        "backend",
        "api",
        "server",
        "auth",
        "database",
        "endpoint",
        "service",
        "crud",
        "authentication",
        "authorization",
        "база",
        "сервер",
        "авторизация",
        "логин",
    ]

    frontend_phrases = [
        "frontend",
        "dashboard",
        "react",
        "vite",
        "landing page",
        "web app",
        "web application",
        "интерфейс",
        "экран",
        "веб демо",
    ]
    frontend_tokens = [
        "ui",
        "web",
        "page",
        "form",
        "screen",
        "website",
        "portal",
        "interface",
        "сайт",
        "экран",
        "интерфейс",
    ]

    fullstack_phrases = [
        "fullstack",
        "full stack",
        "full-stack",
        "with frontend",
        "with ui",
        "with dashboard",
        "и фронтенд",
        "с фронтендом",
        "с интерфейсом",
    ]

    is_mobile = contains_phrase(task_lower, mobile_phrases) or contains_token(task_lower, mobile_tokens)
    is_backend = contains_phrase(task_lower, backend_phrases) or contains_token(task_lower, backend_tokens)
    is_frontend = contains_phrase(task_lower, frontend_phrases) or contains_token(task_lower, frontend_tokens)
    is_fullstack_explicit = contains_phrase(task_lower, fullstack_phrases)
    is_telegram_bot = "telegram" in task_lower and "bot" in task_lower

    if is_mobile and is_backend:
        project_type = ProjectType.FULLSTACK
    elif is_mobile:
        project_type = ProjectType.MOBILE_WEB_DEMO
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

    needs_frontend = project_type in [
        ProjectType.FRONTEND,
        ProjectType.FULLSTACK,
        ProjectType.MOBILE_WEB_DEMO,
    ]
    needs_backend = project_type in [
        ProjectType.BACKEND,
        ProjectType.FULLSTACK,
        ProjectType.TELEGRAM_BOT,
    ]
    needs_mobile = False

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

    tasks.extend(
        [
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
        ]
    )

    return RoutePlan(
        project_type=project_type,
        needs_frontend=needs_frontend,
        needs_backend=needs_backend,
        needs_mobile=needs_mobile,
        tasks=tasks,
    )
