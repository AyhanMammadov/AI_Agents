import os
import subprocess
import shutil


def create_vite_project(base_path):
    if os.path.exists(os.path.join(base_path, "package.json")):
        return

    subprocess.run(
        f"npm.cmd create vite@latest {base_path} -- --template react",
        shell=True
    )

    subprocess.run(
        "npm.cmd install",
        cwd=base_path,
        shell=True
    )


def build_project(result, project_name):
    base_path = os.path.join("workspaces", project_name)

    # 1. create base project (Vite React)
    if not os.path.exists(base_path):
        create_vite_project(base_path)

    src_path = os.path.join(base_path, "src")

    files = result.get("files", [])

    for file in files:
        target_path = os.path.join(src_path, file["path"])

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # rename App.js → App.jsx
        if file["path"] == "App.js":
            target_path = os.path.join(src_path, "App.jsx")

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(file["content"])

    return base_path