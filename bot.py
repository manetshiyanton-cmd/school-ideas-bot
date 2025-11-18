import os
import json
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# === ЛОГИ ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# === GOOGLE SHEETS через GOOGLE_CREDENTIALS_JSON ===
def get_gsheet():
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        sheet_id = os.getenv("SHEET_ID")

        if not creds_json or not sheet_id:
            raise ValueError("❌ GOOGLE_CREDENTIALS_JSON або SHEET_ID не знайдено")

        creds_dict = json.loads(creds_json)

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        return sh.sheet1

    except Exception as e:
        logger.error(f"❌ Помилка Google Sheets: {e}")
        return None


sheet = get_gsheet()


# === ADMIN IDS ===
ADMIN_IDS = [
    int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()
]
logger.info(f"👑 ADMIN_IDS = {ADMIN_IDS}")


# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Напиши ідею — я збережу її в Google Sheets."
    )


# === Команда /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — початок\n"
        "/help — допомога\n"
        "/review — список ідей (адмін)\n"
        "/delete <номер> — видалити ідею (адмін)"
    )


# === Прийом нової ідеї ===
async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if not sheet:
        await update.message.reply_text("⚠️ Немає доступу до Google Sheets.")
        return

    try:
        sheet.append_row([
            text,
            f"@{user.username}" if user.username else user.first_name,
            str(user.id),
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ])

        await update.message.reply_text("✅ Збережено!")

    except Exception as e:
        logger.error(f"❌ Помилка запису: {e}")
        await update.message.reply_text("⚠️ Не вдалося зберегти.")


# === /review для адмінів ===
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Ти не адмін.")
        return

    if not sheet:
        await update.message.reply_text("⚠️ Немає доступу до таблиці.")
        return

    data = sheet.get_all_values()[1:]  # без заголовків

    if not data:
        await update.message.reply_text("💤 Ідей ще нема.")
        return

    text = "\n\n".join(
        f"#{i+1}\nАвтор: {row[1]} (ID {row[2]})\nІдея: {row[0]}\n🕒 {row[3]}"
        for i, row in enumerate(data)
    )

    await update.message.reply_text(text[:4000])


# === /delete для адмінів ===
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Ти не адмін.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Використання: /delete <номер>")
        return

    index = int(context.args[0])

    if not sheet:
        await update.message.reply_text("⚠️ Помилка доступу до таблиці.")
        return

    try:
        data = sheet.get_all_values()

        if index <= 0 or index >= len(data):
            await update.message.reply_text("❌ Такого номера немає.")
            return

        sheet.delete_rows(index + 1)

        await update.message.reply_text(f"🗑️ Видалено #{index}")

    except Exception as e:
        logger.error(f"❌ Помилка видалення: {e}")
        await update.message.reply_text("⚠️ Не вдалося видалити.")


# === ЗАПУСК ===
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не знайдено!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    # === Render Webhook ===
    if os.getenv("RENDER"):
        WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
        PORT = int(os.getenv("PORT", "10000"))

        logger.info("🚀 Запуск через Render webhook")

        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )

    else:
        logger.info("🟢 Локальний запуск (polling)")
        app.run_polling()
