import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, STRONG_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


BACKEND_SYSTEM_PROMPT = """
You are a senior backend engineer.

Your job:
Generate backend code only.

You must return valid JSON with this exact structure:

{
  "files": [
    {
      "path": "backend/main.py",
      "content": "..."
    }
  ]
}

Rules:
- Always return JSON only
- Always include "files"
- files must be a non-empty array
- each file must have:
  - path
  - content
- Never return explanations outside JSON
- For FastAPI projects, include at minimum:
  - main.py
  - requirements.txt

If the task is unclear, still return a minimal valid FastAPI backend scaffold.

Important:
- paths must be exactly:
  - main.py
  - requirements.txt
- do not prefix paths with backend/
- do not wrap files in extra folders
"""


def _extract_backend_input(state) -> dict:
    artifacts_dict = getattr(state, "artifacts", {}) or {}

    payload = {
        "task": state.task,
        "project_type": getattr(state, "project_type", None),
        "backend_retry_feedback": getattr(state, "backend_retry_feedback", None),
    }

    if "spec" in artifacts_dict:
        payload["spec"] = artifacts_dict["spec"].data
    if "architecture" in artifacts_dict:
        payload["architecture"] = artifacts_dict["architecture"].data

    return payload


def _validate_backend_result(result: dict) -> tuple[bool, list[str]]:
    errors = []

    if not isinstance(result, dict):
        return False, ["Backend result is not a dict"]

    files = result.get("files")

    if not isinstance(files, list) or not files:
        errors.append("Backend output does not contain files[]")
        return False, errors

    for i, file in enumerate(files):
        if not isinstance(file, dict):
            errors.append(f"files[{i}] is not an object")
            continue

        if not file.get("path"):
            errors.append(f"files[{i}] missing path")

        if not isinstance(file.get("content"), str):
            errors.append(f"files[{i}] missing content")

    return len(errors) == 0, errors


def _minimal_fallback_backend() -> dict:
    return {
        "files": [
            {
                "path": "main.py",
                "content": '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Generated Backend")

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
def login(payload: LoginRequest):
    if payload.email == "admin@test.com" and payload.password == "123456":
        return {"ok": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
''',
            },
            {
                "path": "requirements.txt",
                "content": "fastapi\nuvicorn\npydantic\n",
            },
        ]
    }


def senior_backend_agent(state) -> dict:
    payload = _extract_backend_input(state)

    try:
        response = client.chat.completions.create(
            model=STRONG_MODEL,
            messages=[
                {"role": "system", "content": BACKEND_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

    except Exception as e:
        fallback = _minimal_fallback_backend()
        return {
            **fallback,
            "contract_ok": True,
            "contract_errors": [],
            "agent_error": str(e),
            "fallback_used": True,
        }

    contract_ok, contract_errors = _validate_backend_result(parsed)

    if not contract_ok and getattr(state, "backend_retry_feedback", None):
        parsed = _minimal_fallback_backend()
        contract_ok, contract_errors = _validate_backend_result(parsed)

    return {
        **parsed,
        "contract_ok": contract_ok,
        "contract_errors": contract_errors,
    }