import os
import subprocess
import sys
import time
import socket
from pathlib import Path

# Cross-platform npm: on Windows npm is a .cmd file and needs npm.cmd
_NPM = ["npm.cmd"] if sys.platform == "win32" else ["npm"]


def _is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _wait_for_port(port: int, timeout: int = 20, host: str = "127.0.0.1") -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if _is_port_open(port, host):
            return True
        time.sleep(1)
    return False


def _find_free_port(start: int, host: str = "127.0.0.1", attempts: int = 50) -> int:
    for port in range(start, start + attempts):
        if not _is_port_open(port, host):
            return port
    return start


def start_backend(backend_path: str, port: int = 8000) -> dict:
    logs_dir = Path(backend_path) / ".logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Install dependencies before starting
    req_file = Path(backend_path) / "requirements.txt"
    if req_file.exists():
        print(f"\n📦 Installing backend dependencies...")
        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
            cwd=backend_path,
            capture_output=True,
            text=True,
        )
        if pip_result.returncode != 0:
            return {
                "ok": False,
                "error": "pip install failed",
                "stderr": pip_result.stderr[:2000],
                "url": None,
                "health_url": None,
            }
        print("✅ Backend dependencies installed")

    stdout_file = open(logs_dir / "backend_stdout.log", "w", encoding="utf-8")
    stderr_file = open(logs_dir / "backend_stderr.log", "w", encoding="utf-8")

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=backend_path,
        stdout=stdout_file,
        stderr=stderr_file,
        shell=False,
    )

    started = _wait_for_port(port, timeout=20)

    return {
        "ok": started,
        "pid": process.pid if started else None,
        "url": f"http://127.0.0.1:{port}",
        "health_url": f"http://127.0.0.1:{port}/health",
        "stdout_log": str(logs_dir / "backend_stdout.log"),
        "stderr_log": str(logs_dir / "backend_stderr.log"),
    }


def start_frontend(frontend_path: str, port: int = 5173) -> dict:
    port = _find_free_port(port)
    logs_dir = Path(frontend_path) / ".logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    stdout_file = open(logs_dir / "frontend_stdout.log", "w", encoding="utf-8")
    stderr_file = open(logs_dir / "frontend_stderr.log", "w", encoding="utf-8")

    process = subprocess.Popen(
        [*_NPM, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)],
        cwd=frontend_path,
        stdout=stdout_file,
        stderr=stderr_file,
        shell=False,
    )

    started = _wait_for_port(port, timeout=25)

    return {
        "ok": started,
        "pid": process.pid if started else None,
        "url": f"http://127.0.0.1:{port}",
        "stdout_log": str(logs_dir / "frontend_stdout.log"),
        "stderr_log": str(logs_dir / "frontend_stderr.log"),
    }
