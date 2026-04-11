import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from app.config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, TRANSCRIBE_MODEL
from app.orchestrator import run_orchestrator

client = OpenAI(api_key=OPENAI_API_KEY)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет. Я твой AI assistant.\n"
        "Можешь писать текстом или отправить voice."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        response = run_orchestrator(text)
        await update.message.reply_text(str(response)[:4000])
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке текста: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp_path = "temp_voice.ogg"

    try:
        await update.message.reply_text("Принял voice. Распознаю...")

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

        response = run_orchestrator(voice_text)
        await update.message.reply_text(str(response)[:4000])

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

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()