import os
import subprocess
import time
import socket


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_free_port(start=3000, end=9000):
    for port in range(start, end):
        if not is_port_open(port):
            return port
    return None


def run_command(command, cwd):
    return subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def deploy_agent(context: dict) -> dict:
    workspace = context.get("workspace")

    if not workspace or not os.path.exists(workspace):
        return {"error": "workspace not found"}

    files = []
    for root, _, filenames in os.walk(workspace):
        for f in filenames:
            files.append(os.path.join(root, f))

    has_package_json = any("package.json" in f for f in files)

    if not has_package_json:
        return {
            "error": "No runnable frontend/backend detected",
            "hint": "Need package.json or requirements.txt"
        }

    try:
        # 1. install deps
        subprocess.run("npm install", cwd=workspace, shell=True)

        # 2. find port
        port = 5173  # default vite
        if is_port_open(port):
            port = find_free_port()

        # 3. run dev server
        process = run_command("npm run dev", workspace)

        # 4. wait until server starts
        for _ in range(15):
            time.sleep(1)
            if is_port_open(port):
                break

        url = f"http://localhost:{port}"

        return {
            "role": "deploy",
            "deliverables": {
                "status": "RUNNING",
                "url": url,
                "message": "Application is live"
            },
            "process_id": process.pid
        }

    except Exception as e:
        return {
            "error": str(e)
        }