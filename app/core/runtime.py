import os
from app.core.state_store import ProjectState


def write_files(base_path: str, files: list):
    for file in files:
        file_path = os.path.join(base_path, file["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file["content"])


def apply_generated_code(state: ProjectState):
    """
    Берет артефакты от агентов и записывает файлы на диск.
    """

    if state.has_artifact("backend_code"):
        backend_artifact = state.get_artifact("backend_code")
        backend_files = backend_artifact.data.get("files", [])

        backend_path = os.path.join(state.workspace, "backend")
        os.makedirs(backend_path, exist_ok=True)

        write_files(backend_path, backend_files)

    if state.has_artifact("frontend_code"):
        frontend_artifact = state.get_artifact("frontend_code")

        if not frontend_artifact.data.get("contract_ok", False):
            print("\n❌ FRONTEND FILE WRITE SKIPPED")
            print(frontend_artifact.data.get("contract_errors", []))
        else:
            frontend_files = frontend_artifact.data.get("files", [])

            frontend_path = os.path.join(state.workspace, "frontend")
            os.makedirs(frontend_path, exist_ok=True)

            write_files(frontend_path, frontend_files)

    if state.has_artifact("mobile_code"):
        mobile_artifact = state.get_artifact("mobile_code")
        mobile_files = mobile_artifact.data.get("files", [])

        mobile_path = os.path.join(state.workspace, "mobile")
        os.makedirs(mobile_path, exist_ok=True)

        write_files(mobile_path, mobile_files)