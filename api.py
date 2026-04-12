from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from main import run_system

app = FastAPI(title="AI Agents API")


class TaskRequest(BaseModel):
    task: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_task(payload: TaskRequest) -> dict[str, Any]:
    task = payload.task.strip()

    if not task:
        raise HTTPException(status_code=400, detail="Task is empty")

    result = run_system(task)

    if hasattr(result, "snapshot"):
        return {
            "ok": True,
            "state": result.snapshot(),
        }

    return {
        "ok": True,
        "result": result,
    }