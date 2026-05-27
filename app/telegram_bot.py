import os

from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from app.config import (
    ALLOWED_TELEGRAM_USER_IDS,
    OPENAI_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TRANSCRIBE_MODEL,
    is_telegram_user_allowed,
)
from main import run_system

client = OpenAI(api_key=OPENAI_API_KEY)


def _allowed(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else None
    return is_telegram_user_allowed(user_id)


def format_response(result: dict) -> str:
    if not isinstance(result, dict):
        return str(result)

    if not result.get("ok"):
        return f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"

    mode = result.get("mode")

    if mode in {"simple_answer", "business_task"}:
        return result.get("answer", "Пустой ответ")

    if mode == "build_project" or "workspace" in result:
        lines = [
            "Проект обработан.",
        ]

        if result.get("project_type"):
            lines.append(f"Тип проекта: {result['project_type']}")

        if result.get("workspace"):
            lines.append(f"Workspace: {result['workspace']}")

        auto_run_result = result.get("auto_run_result") or {}
        frontend = auto_run_result.get("frontend") or {}
        backend = auto_run_result.get("backend") or {}
        railway = auto_run_result.get("railway") or {}

        if frontend.get("url"):
            lines.append(f"Frontend: {frontend['url']}")

        if railway.get("public_url"):
            lines.append(f"Railway: {railway['public_url']}")
        elif railway.get("message"):
            lines.append(f"Railway: {railway['message']}")

        if backend.get("url"):
            lines.append(f"Backend: {backend['url']}")

        if backend.get("health_url"):
            lines.append(f"Health: {backend['health_url']}")

        if result.get("pipeline_error"):
            lines.append(f"Pipeline error: {result['pipeline_error']}")

        errors = auto_run_result.get("errors") or []
        if errors:
            lines.append("Errors:")
            lines.extend(str(error)[:700] for error in errors[:3])

        token_usage = result.get("token_usage") or {}
        if token_usage.get("total_tokens") is not None:
            lines.append(f"Tokens: {token_usage.get('total_tokens', 0)}")

        return "\n".join(lines)

    return str(result)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        await update.message.reply_text("Access denied.")
        return

    await update.message.reply_text(
        "Привет.\n"
        "Я твой AI assistant.\n"
        "Можешь писать текстом или отправить voice."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        await update.message.reply_text("Access denied.")
        return

    text = update.message.text

    try:
        response = run_system(text)
        message = format_response(response)
        print("\nTELEGRAM RESULT:")
        print(message[:4000])
        await update.message.reply_text(message[:4000])

    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке текста: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        await update.message.reply_text("Access denied.")
        return

    temp_path = "temp_voice.ogg"

    try:
        await update.message.reply_text("Принял voice.\nРаспознаю...")

        voice = update.message.voice
        voice_file = await voice.get_file()
        await voice_file.download_to_drive(temp_path)

        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=TRANSCRIBE_MODEL,
                file=audio_file,
                response_format="text",
            )

        voice_text = transcription.text if hasattr(transcription, "text") else str(transcription)

        await update.message.reply_text(f"Ты сказал:\n{voice_text[:4000]}")

        response = run_system(voice_text)
        message = format_response(response)
        print("\nTELEGRAM RESULT:")
        print(message[:4000])
        await update.message.reply_text(message[:4000])

    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке voice: {e}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def run_telegram_bot():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY не найден в .env")

    if not ALLOWED_TELEGRAM_USER_IDS:
        print("Warning: ALLOWED_TELEGRAM_USER_IDS is empty, Telegram bot accepts any user.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()
