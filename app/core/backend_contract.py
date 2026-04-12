def _files_map(files: list) -> dict:
    result = {}
    for item in files:
        path = item.get("path")
        content = item.get("content", "")
        if path:
            result[path.replace("\\", "/")] = content
    return result


REQUIRED_BACKEND_FILES = {
    "main.py",
    "requirements.txt",
}


def validate_backend_artifact(data: dict) -> dict:
    errors = []

    if not isinstance(data, dict):
        return {"ok": False, "errors": ["Backend output is not a dict"]}

    files = data.get("files")
    if not isinstance(files, list) or not files:
        return {"ok": False, "errors": ["Backend output does not contain files[]"]}

    file_map = _files_map(files)

    missing = [f for f in REQUIRED_BACKEND_FILES if f not in file_map]
    if missing:
        errors.append(f"Missing required files: {missing}")

    main_py = file_map.get("main.py", "")
    requirements_txt = file_map.get("requirements.txt", "")

    if "FastAPI" not in main_py:
        errors.append("main.py must contain FastAPI")

    if "app = FastAPI(" not in main_py and "app=FastAPI(" not in main_py:
        errors.append("main.py must define app = FastAPI()")

    if "/health" not in main_py:
        errors.append("main.py must contain /health endpoint")

    req_lower = requirements_txt.lower()
    if "fastapi" not in req_lower:
        errors.append("requirements.txt must contain fastapi")

    if "uvicorn" not in req_lower:
        errors.append("requirements.txt must contain uvicorn")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }