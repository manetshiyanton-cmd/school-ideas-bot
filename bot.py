import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------- GOOGLE SHEETS ---------------- #

def get_gsheet():
    try:
        google_creds_json = os.getenv("GOOGLE_CREDS_JSON")
        if not google_creds_json:
            raise Exception("GOOGLE_CREDS_JSON is missing")

        creds = Credentials.from_service_account_info(
            eval(google_creds_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        client = gspread.authorize(creds)

        sheet = client.open("school_ideas").sheet1
        logger.info("✅ Google Sheets connected")

        return sheet

    except Exception as e:
        logger.error(f"❌ Google Sheets error: {e}")
        return None


sheet = get_gsheet()

# ---------------- BOT LOGIC ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Надсилай свою ідею 👇")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if sheet:
        sheet.append_row([update.effective_user.id, update.effective_user.full_name, text])
        await update.message.reply_text("🟢 Ідею додано!")
    else:
        await update.message.reply_text("🔴 Помилка! Google Sheets недоступний.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if sheet:
        data = sheet.get_all_values()
        msg = "\n".join([f"{row[1]}: {row[2]}" for row in data[1:]])
        await update.message.reply_text(msg if msg else "Поки ідей нема 😅")
    else:
        await update.message.reply_text("Sheets недоступний.")

# ---------------- START BOT ---------------- #

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
