import os
import subprocess

from app.core.process_runner import start_backend, start_frontend
from app.core.railway_deploy import deploy_frontend_to_railway
from app.core.validator_runtime import check_health
from app.core.frontend_runtime_validator import validate_frontend_runtime


def find_real_project_dir(base_path: str, target_file: str):
    if os.path.isfile(os.path.join(base_path, target_file)):
        return base_path

    for root, dirs, files in os.walk(base_path):
        if target_file in files:
            return root

    return None


def _runtime_error_summary(check: dict) -> str:
    stage = check.get("stage", "unknown")
    stderr = (check.get("stderr") or "").strip()
    stdout = (check.get("stdout") or "").strip()
    details = stderr or stdout or "no output"
    details = details[-1200:]
    return f"Frontend build validation failed at {stage}: {details}"


def auto_run_project(state) -> dict:
    frontend_artifact = state.get_artifact("frontend_code") if state.has_artifact("frontend_code") else None
    backend_artifact = state.get_artifact("backend_code") if state.has_artifact("backend_code") else None

    if backend_artifact and not backend_artifact.data.get("contract_ok", False):
        return {
            "ok": False,
            "backend": None,
            "frontend": None,
            "health": None,
            "errors": ["Backend contract validation failed before auto-run"],
            "backend_contract_errors": backend_artifact.data.get("contract_errors", []),
        }

    if frontend_artifact and not frontend_artifact.data.get("contract_ok", False):
        return {
            "ok": False,
            "backend": None,
            "frontend": None,
            "health": None,
            "errors": ["Frontend contract validation failed before auto-run"],
            "frontend_contract_errors": frontend_artifact.data.get("contract_errors", []),
        }

    workspace = state.workspace

    backend_base = os.path.join(workspace, "backend")
    frontend_base = os.path.join(workspace, "frontend")

    needs_backend = state.project_type in ["backend", "fullstack", "telegram_bot"]
    needs_frontend = state.project_type in ["frontend", "fullstack", "mobile_web_demo"]

    backend_path = find_real_project_dir(backend_base, "main.py") if needs_backend and os.path.isdir(backend_base) else None
    frontend_path = find_real_project_dir(frontend_base, "package.json") if needs_frontend and os.path.isdir(frontend_base) else None

    result = {
        "ok": False,
        "backend": None,
        "frontend": None,
        "railway": None,
        "health": None,
        "errors": [],
        "resolved_paths": {
            "backend": backend_path,
            "frontend": frontend_path,
        }
    }

    if needs_backend:
        if backend_path:
            backend_result = start_backend(backend_path, port=8000)
            result["backend"] = backend_result

            if not backend_result["ok"]:
                result["errors"].append("Backend did not start")
        else:
            result["errors"].append("Backend project folder not found")

    if result["backend"] and result["backend"]["ok"]:
        health_result = check_health(result["backend"]["health_url"])
        result["health"] = health_result

        if not health_result["ok"]:
            result["errors"].append("Health check failed")

    if needs_frontend:
        if frontend_path:
            runtime_check = validate_frontend_runtime(frontend_path)
            result["frontend_runtime_check"] = runtime_check

            if not runtime_check["ok"]:
                first_error = _runtime_error_summary(runtime_check)
                print(f"\n❌ {first_error}")
                result["errors"].append(first_error)

                state.frontend_retry_feedback = {
                    "retry_mode": True,
                    "runtime_stage": runtime_check.get("stage"),
                    "runtime_stdout": runtime_check.get("stdout", ""),
                    "runtime_stderr": runtime_check.get("stderr", ""),
                    "contract_errors": [],
                }

                if state.has_artifact("frontend_code"):
                    from app.agents.registry import frontend_wrapper

                    print("\n⚠️ FRONTEND BUILD FAILED — RETRYING ONCE WITH RUNTIME ERROR")
                    retry_artifact = frontend_wrapper(state)
                    state.add_artifact(retry_artifact)
                    state.log_step("frontend_runtime_retry", retry_artifact.ref)
                    state.frontend_retry_feedback = None

                    retry_data = retry_artifact.data if isinstance(retry_artifact.data, dict) else {}

                    if retry_data.get("contract_ok", False):
                        from app.core.runtime import apply_generated_code

                        apply_generated_code(state)

                        frontend_path = find_real_project_dir(frontend_base, "package.json")
                        result["resolved_paths"]["frontend"] = frontend_path

                        second_runtime_check = validate_frontend_runtime(frontend_path)
                        result["frontend_runtime_retry_check"] = second_runtime_check

                        if second_runtime_check["ok"]:
                            frontend_result = start_frontend(frontend_path, port=5173)
                            result["frontend"] = frontend_result

                            result["errors"] = [
                                e for e in result["errors"]
                                if e != first_error
                            ]

                            if not frontend_result["ok"]:
                                result["errors"].append("Frontend did not start")
                            else:
                                result["railway"] = deploy_frontend_to_railway(frontend_path)
                        else:
                            retry_error = _runtime_error_summary(second_runtime_check)
                            print(f"\n❌ {retry_error}")
                            if state.project_type == "mobile_web_demo":
                                from app.core.frontend_fallback import build_mobile_web_demo_fallback
                                from app.core.runtime import apply_generated_code
                                from app.core.schemas import Artifact

                                print("\n⚠️ USING MOBILE WEB DEMO FALLBACK AFTER RUNTIME RETRY FAILED")
                                fallback_artifact = Artifact(
                                    ref="frontend_code",
                                    kind="frontend_code",
                                    data=build_mobile_web_demo_fallback(
                                        state.task,
                                        f"runtime retry failed: {retry_error}",
                                    ),
                                )
                                state.add_artifact(fallback_artifact)
                                state.log_step("frontend_runtime_fallback", fallback_artifact.ref)
                                apply_generated_code(state)

                                frontend_path = find_real_project_dir(frontend_base, "package.json")
                                result["resolved_paths"]["frontend"] = frontend_path
                                fallback_runtime_check = validate_frontend_runtime(frontend_path)
                                result["frontend_runtime_fallback_check"] = fallback_runtime_check

                                if fallback_runtime_check["ok"]:
                                    frontend_result = start_frontend(frontend_path, port=5173)
                                    result["frontend"] = frontend_result
                                    result["errors"] = []
                                    if not frontend_result["ok"]:
                                        result["errors"].append("Frontend did not start")
                                    else:
                                        result["railway"] = deploy_frontend_to_railway(frontend_path)
                                else:
                                    result["errors"].append(
                                        f"Frontend fallback build failed: {_runtime_error_summary(fallback_runtime_check)}"
                                    )
                            else:
                                result["errors"].append(f"Frontend build validation failed after retry: {retry_error}")
                    else:
                        result["errors"].append("Frontend contract failed after runtime retry")
            else:
                frontend_result = start_frontend(frontend_path, port=5173)
                result["frontend"] = frontend_result

                if not frontend_result["ok"]:
                    result["errors"].append("Frontend did not start")
                else:
                    result["railway"] = deploy_frontend_to_railway(frontend_path)
        else:
            result["errors"].append("Frontend project folder not found")

    result["ok"] = len(result["errors"]) == 0
    return result
