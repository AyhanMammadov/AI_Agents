from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from telegram import Update, Bot

from app.config import (
    API_RUN_TOKEN,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
    is_telegram_user_allowed,
)
from main import run_system

app = FastAPI(title="AI Agents API")

telegram_bot = None
if TELEGRAM_BOT_TOKEN:
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)


class TaskRequest(BaseModel):
    task: str


def _require_api_token(req: Request):
    if not API_RUN_TOKEN:
        return

    auth_header = req.headers.get("authorization", "")
    bearer = auth_header.removeprefix("Bearer ").strip()
    api_key = req.headers.get("x-api-key", "").strip()
    if API_RUN_TOKEN not in {bearer, api_key}:
        raise HTTPException(status_code=403, detail="Invalid API token")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "AI Agents API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/debug-api")
def debug_api():
    return {
        "version": "api_v2_bot_webhook",
        "uses": "telegram.Bot",
    }

@app.post("/run")
def run_task(payload: TaskRequest, req: Request) -> dict[str, Any]:
    _require_api_token(req)

    task = payload.task.strip()

    if not task:
        raise HTTPException(status_code=400, detail="Task is empty")

    result = run_system(task)
    return result


@app.post("/webhook")
async def telegram_webhook(req: Request) -> dict[str, Any]:
    if telegram_bot is None:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN not configured")

    if TELEGRAM_WEBHOOK_SECRET:
        secret = req.headers.get("x-telegram-bot-api-secret-token", "")
        if secret != TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    try:
        data = await req.json()
        update = Update.de_json(data, telegram_bot)

        user_id = update.effective_user.id if update.effective_user else None
        if not is_telegram_user_allowed(user_id):
            return {"ok": True, "ignored": True}

        if update.message and update.message.text:
            user_text = update.message.text

            try:
                result = run_system(user_text)
            except Exception as e:
                await telegram_bot.send_message(
                    chat_id=update.message.chat_id,
                    text=f"Ошибка внутри системы: {str(e)[:3500]}",
                )
                return {"ok": True}

            reply = "Произошла ошибка"

            mode = result.get("mode")

            if mode in {"simple_answer", "business_task"}:
                reply = result.get("answer", "Пустой ответ")

            elif mode == "build_project":
                workspace = result.get("workspace")
                project_type = result.get("project_type")
                pipeline_error = result.get("pipeline_error")
                auto_run_result = result.get("auto_run_result") or {}
                frontend = auto_run_result.get("frontend") or {}
                railway = auto_run_result.get("railway") or {}
                preview = railway.get("public_url") or frontend.get("url")

                if pipeline_error:
                    reply = f"Проект не собрался.\nОшибка: {pipeline_error}"
                else:
                    reply = (
                        "Проект обработан.\n"
                        f"Тип: {project_type}\n"
                        f"Workspace: {workspace}"
                    )

                    if preview:
                        reply += f"\nPreview: {preview}"

                    errors = auto_run_result.get("errors") or []
                    if errors:
                        reply += "\nErrors:\n" + "\n".join(str(error)[:700] for error in errors[:3])

                    token_usage = result.get("token_usage") or {}
                    if token_usage.get("total_tokens") is not None:
                        reply += f"\nTokens: {token_usage.get('total_tokens', 0)}"

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

            await telegram_bot.send_message(
                chat_id=update.message.chat_id,
                text=reply[:4000],
            )

    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")

    return {"ok": True}
