import json
import posixpath
import re


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


def _contains_jsx(content: str) -> bool:
    return bool(re.search(r"return\s*\(|=>\s*\(|const\s+\w+\s*=\s*\([^)]*\)\s*=>", content)) and bool(
        re.search(r"<[A-Z_a-z][A-Za-z0-9_.:-]*(\s|>|/>)", content)
    )


def _resolve_relative_import(current_path: str, specifier: str, file_map: dict) -> bool:
    if not specifier.startswith("."):
        return True

    base_dir = posixpath.dirname(current_path)
    raw_target = posixpath.normpath(posixpath.join(base_dir, specifier))

    if posixpath.splitext(raw_target)[1]:
        return raw_target in file_map

    candidates = [
        raw_target,
        f"{raw_target}.js",
        f"{raw_target}.jsx",
        f"{raw_target}.css",
        f"{raw_target}.json",
        posixpath.join(raw_target, "index.js"),
        posixpath.join(raw_target, "index.jsx"),
    ]
    return any(candidate in file_map for candidate in candidates)


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

    for path, content in file_map.items():
        if path.startswith("src/") and path.endswith(".js") and _contains_jsx(content):
            errors.append(f"{path} contains JSX but uses .js extension; rename it to .jsx and update imports")

        if path.endswith((".js", ".jsx")):
            import_specs = re.findall(r"from\s+['\"]([^'\"]+)['\"]", content)
            import_specs.extend(re.findall(r"import\s+['\"]([^'\"]+)['\"]", content))
            for specifier in import_specs:
                if not _resolve_relative_import(path, specifier, file_map):
                    errors.append(f"{path} imports missing local file: {specifier}")

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
