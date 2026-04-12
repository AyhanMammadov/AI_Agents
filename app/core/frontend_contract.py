import json


REQUIRED_FRONTEND_FILES = {
    "package.json",
    "index.html",
    "vite.config.js",
    "src/main.jsx",
    "src/App.jsx",
}


def _files_map(files: list) -> dict:
    result = {}
    for item in files:
        path = item.get("path")
        content = item.get("content", "")
        if path:
            result[path.replace("\\", "/")] = content
    return result


def validate_frontend_artifact(data: dict) -> dict:
    errors = []

    if not isinstance(data, dict):
        return {"ok": False, "errors": ["Frontend output is not a dict"]}

    files = data.get("files")
    if not isinstance(files, list) or not files:
        return {"ok": False, "errors": ["Frontend output does not contain files[]"]}

    file_map = _files_map(files)

    missing = [f for f in REQUIRED_FRONTEND_FILES if f not in file_map]
    if missing:
        errors.append(f"Missing required files: {missing}")

    if "src/index.html" in file_map:
        errors.append("index.html must be in project root, not in src/")

    package_json_raw = file_map.get("package.json")
    if not package_json_raw:
        errors.append("package.json is missing")
    else:
        try:
            package_json = json.loads(package_json_raw)
            scripts = package_json.get("scripts", {})

            if scripts.get("dev") != "vite":
                errors.append("package.json scripts.dev must be 'vite'")

            if scripts.get("build") != "vite build":
                errors.append("package.json scripts.build must be 'vite build'")

            if scripts.get("preview") != "vite preview":
                errors.append("package.json scripts.preview must be 'vite preview'")
        except Exception as e:
            errors.append(f"package.json is invalid JSON: {e}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }