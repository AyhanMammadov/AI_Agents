import subprocess


def validate_frontend_runtime(frontend_path: str) -> dict:
    try:
        install_result = subprocess.run(
            ["cmd", "/c", "npm", "install"],
            cwd=frontend_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            shell=False,
        )

        if install_result.returncode != 0:
            return {
                "ok": False,
                "stage": "npm_install",
                "stdout": install_result.stdout,
                "stderr": install_result.stderr,
            }

        build_result = subprocess.run(
            ["cmd", "/c", "npm", "run", "build"],
            cwd=frontend_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            shell=False,
        )

        return {
            "ok": build_result.returncode == 0,
            "stage": "npm_build",
            "stdout": build_result.stdout,
            "stderr": build_result.stderr,
        }

    except Exception as e:
        return {
            "ok": False,
            "stage": "exception",
            "stdout": "",
            "stderr": str(e),
        }