def create_project_memory(task: str):
    return {
        "user_task": task,

        # 📌 Бизнес уровень
        "project_intent": "",
        "target_users": [],
        "features": [],
        "requirements": {},

        # 🏗 Архитектура
        "architecture": {},

        # 🧠 Коллективное знание
        "decisions": [],
        "constraints": [],
        "assumptions": [],
        "open_questions": [],

        # 📦 Артефакты по агентам
        "artifacts": {
            "product_owner": {},
            "business_analyst": {},
            "architect": {},
            "backend": {},
            "frontend": {},
            "qa": {},
        }
    }


def _safe_extend_unique(target_list, new_items):
    if not isinstance(new_items, list):
        return

    for item in new_items:
        if item and item not in target_list:
            target_list.append(item)


def update_memory(memory, agent_output):
    role = agent_output.get("role")

    # --- decisions / assumptions / questions ---
    _safe_extend_unique(memory["decisions"], agent_output.get("decisions", []))
    _safe_extend_unique(memory["assumptions"], agent_output.get("assumptions", []))
    _safe_extend_unique(memory["open_questions"], agent_output.get("open_questions", []))

    # --- deliverables → artifacts ---
    deliverables = agent_output.get("deliverables", {})

    if isinstance(deliverables, dict) and role:
        if role not in memory["artifacts"]:
            memory["artifacts"][role] = {}

        memory["artifacts"][role].update(deliverables)

    return memory