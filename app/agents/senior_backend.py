import json
from openai import OpenAI

from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.core.schemas import Artifact

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
  - backend/main.py
  - backend/requirements.txt

If the task is unclear, still return a minimal valid backend scaffold.
"""


def _extract_backend_input(state) -> dict:
    return {
        "task": state.task,
        "project_type": getattr(state, "project_type", None),
        "artifacts": [artifact.ref for artifact in getattr(state, "artifacts", [])],
        "backend_retry_feedback": getattr(state, "backend_retry_feedback", None),
    }


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
                "path": "backend/main.py",
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
                "path": "backend/requirements.txt",
                "content": "fastapi\nuvicorn\npydantic\n",
            },
        ]
    }


def senior_backend_agent(state) -> Artifact:
    payload = _extract_backend_input(state)

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": BACKEND_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)

    except Exception as e:
        fallback = _minimal_fallback_backend()
        return Artifact(
            ref="backend_code",
            data={
                **fallback,
                "contract_ok": True,
                "contract_errors": [],
                "agent_error": str(e),
                "fallback_used": True,
            },
        )

    contract_ok, contract_errors = _validate_backend_result(parsed)

    if not contract_ok and getattr(state, "backend_retry_feedback", None):
        parsed = _minimal_fallback_backend()
        contract_ok, contract_errors = _validate_backend_result(parsed)

    return Artifact(
        ref="backend_code",
        data={
            **parsed,
            "contract_ok": contract_ok,
            "contract_errors": contract_errors,
        },
    )