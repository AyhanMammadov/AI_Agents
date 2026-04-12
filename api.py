import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from telegram import Update
from telegram.ext import ApplicationBuilder

from main import run_system

app = FastAPI(title="AI Agents API")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

telegram_app = None
if TELEGRAM_BOT_TOKEN:
    telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


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
    return result


@app.post("/webhook")
async def telegram_webhook(req: Request) -> dict[str, Any]:
    if telegram_app is None:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")

    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)

    if update.message and update.message.text:
        user_text = update.message.text
        result = run_system(user_text)

        reply = "Произошла ошибка"

        mode = result.get("mode")

        if mode in {"simple_answer", "business_task"}:
            reply = result.get("answer", "Пустой ответ")

        elif mode == "build_project":
            workspace = result.get("workspace")
            project_type = result.get("project_type")
            pipeline_error = result.get("pipeline_error")

            if pipeline_error:
                reply = f"Проект не собрался.\nОшибка: {pipeline_error}"
            else:
                reply = (
                    "Проект обработан.\n"
                    f"Тип: {project_type}\n"
                    f"Workspace: {workspace}"
                )

        elif mode == "status_request":
            workspace = result.get("workspace")
            project_type = result.get("project_type")
            reply = (
                "Статус последнего результата:\n"
                f"Тип: {project_type}\n"
                f"Workspace: {workspace}"
            )

        elif result.get("error"):
            reply = f"Ошибка: {result.get('error')}"

        await telegram_app.bot.send_message(
            chat_id=update.message.chat_id,
            text=reply[:4000],
        )

    return {"ok": True}