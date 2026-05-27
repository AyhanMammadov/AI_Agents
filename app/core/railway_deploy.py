import os
import shutil
import subprocess

from app.config import RAILWAY_DEPLOY_ENABLED, RAILWAY_PUBLIC_URL, RAILWAY_SERVICE_NAME


def deploy_frontend_to_railway(frontend_path: str) -> dict:
    """Optional Railway deployment for generated frontend demos.

    The default is intentionally non-destructive and token-saving: prepare the
    project for Railway, but do not deploy unless explicitly enabled in env.
    """

    result = {
        "ok": False,
        "skipped": True,
        "provider": "railway",
        "path": frontend_path,
        "public_url": RAILWAY_PUBLIC_URL or None,
        "message": "",
    }

    if not RAILWAY_DEPLOY_ENABLED:
        result["message"] = "Railway deploy is disabled. Set RAILWAY_DEPLOY_ENABLED=true when Railway CLI is configured."
        return result

    railway_bin = shutil.which("railway")
    if not railway_bin:
        result["message"] = "Railway CLI was not found. Install it and run railway login/link first."
        return result

    command = [railway_bin, "up", "--detach"]
    if RAILWAY_SERVICE_NAME:
        command.extend(["--service", RAILWAY_SERVICE_NAME])

    env = os.environ.copy()
    try:
        completed = subprocess.run(
            command,
            cwd=frontend_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env=env,
        )
    except Exception as exc:
        result["message"] = str(exc)
        return result

    result.update(
        {
            "ok": completed.returncode == 0,
            "skipped": False,
            "command": " ".join(command),
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "message": "Railway deploy command completed" if completed.returncode == 0 else "Railway deploy failed",
        }
    )
    return result
