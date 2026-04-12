import os
import subprocess
import sys
import time
import socket
from pathlib import Path


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


def start_backend(backend_path: str, port: int = 8000) -> dict:
    logs_dir = Path(backend_path) / ".logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

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
    logs_dir = Path(frontend_path) / ".logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    stdout_file = open(logs_dir / "frontend_stdout.log", "w", encoding="utf-8")
    stderr_file = open(logs_dir / "frontend_stderr.log", "w", encoding="utf-8")

    process = subprocess.Popen(
        ["cmd", "/c", "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)],
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