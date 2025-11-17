import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# -------------------- ЛОГУВАННЯ --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------- НАЛАШТУВАННЯ --------------------
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("❌ BOT_TOKEN не знайдено в ENV!")
    raise SystemExit

ADMIN_IDS = [1407696674, 955785809]
logger.info(f"👑 ADMIN_IDS = {ADMIN_IDS}")

# -------------------- GOOGLE SHEETS ПІДКЛЮЧЕННЯ --------------------
def get_gsheet():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds_json = os.getenv("GOOGLE_CREDS_JSON")
        if not creds_json:
            logger.error("❌ GOOGLE_CREDS_JSON ПУСТЕ!")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            eval(creds_json),
            scope
        )
        client = gspread.authorize(creds)
        sheet = client.open("school_ideas").sheet1
        return sheet
    except Exception as e:
        logger.error(f"❌ Помилка підключення до Google Sheets: {e}")
        return None

sheet = get_gsheet()

# -------------------- ОБРОБНИК ПОВІДОМЛЕНЬ --------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    logger.info(f"💬 Отримано: {user.id} — {text}")

    # записуємо в Google Sheets
    if sheet:
        try:
            sheet.append_row([str(user.id), user.full_name, text])
            logger.info("📌 Записано в Google Sheets")
        except Exception as e:
            logger.error(f"❌ Не вдалось записати в таблицю: {e}")

    await update.message.reply_text("✔️ Прийнято!")

# -------------------- ЗАПУСК --------------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Запуск через webhook на Render")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
