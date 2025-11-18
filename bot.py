import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)

# --- GOOGLE SHEETS CONNECT ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(
    "creds.json", scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open("AI ideas").sheet1


# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бро, я на зв’язку. Пиши ідею 👇")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # запис у Google Sheets
    try:
        sheet.append_row([text])
        await update.message.reply_text("Додав у табличку ✔️")
    except Exception as e:
        await update.message.reply_text("Помилка підключення до таблиці ❌")
        logging.error(e)


# --- MAIN ---
def main():
    app = ApplicationBuilder().token("ТВОЙ_ТОКЕН").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
