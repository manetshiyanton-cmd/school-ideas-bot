import os
import json
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === GOOGLE SHEETS ===
SHEET_ID = os.getenv("SHEET_ID")
SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")

gc = None
worksheet = None

if SHEET_ID and SERVICE_JSON:
    try:
        creds_json = json.loads(SERVICE_JSON)
        creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.sheet1
        logger.info("✅ Підключено до Google Sheets")
    except Exception as e:
        logger.error(f"❌ Помилка підключення до Google Sheets: {e}")
else:
    logger.warning("⚠️ Google Sheets не налаштовано (SHEET_ID або GOOGLE_SERVICE_JSON відсутній)")

# === ФАЙЛ ІДЕЙ ДЛЯ ЛОКАЛЬНОГО ЗБЕРЕЖЕННЯ ===
IDEAS_FILE = "ideas.json"

def load_ideas():
    if os.path.exists(IDEAS_FILE):
        try:
            with open(IDEAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_ideas(ideas):
    with open(IDEAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)

ideas = load_ideas()

# === КОМАНДИ БОТА ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли мені свою ідею, і я її збережу!")

async def show_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ideas:
        await update.message.reply_text("Поки що немає жодної ідеї 😢")
    else:
        text = "\n".join(f"{i+1}. {idea['text']}" for i, idea in enumerate(ideas))
        await update.message.reply_text(f"💡 Ідеї:\n{text}")

async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Будь ласка, напиши ідею текстом 😉")
        return

    user = update.message.from_user
    idea = {
        "text": text,
        "user": f"@{user.username}" if user.username else f"{user.first_name}",
        "user_id": user.id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    ideas.append(idea)
    save_ideas(ideas)

    # === Додавання в Google Sheets ===
    if worksheet:
        try:
            worksheet.append_row([idea["text"], idea["user"], idea["user_id"], idea["time"]])
        except Exception as e:
            logger.error(f"⚠️ Помилка запису в Google Sheets: {e}")

    await update.message.reply_text("✅ Ідею збережено!")

async def delete_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
    user_id = str(update.message.from_user.id)

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Ця команда лише для адміністраторів.")
        return

    if not context.args:
        await update.message.reply_text("Вкажи номер ідеї для видалення. Наприклад: /delete 2")
        return

    try:
        index = int(context.args[0]) - 1
        if 0 <= index < len(ideas):
            deleted = ideas.pop(index)
            save_ideas(ideas)
            await update.message.reply_text(f"🗑 Ідею \"{deleted['text']}\" видалено.")
        else:
            await update.message.reply_text("Неправильний номер ідеї.")
    except ValueError:
        await update.message.reply_text("Вкажи номер правильно, наприклад: /delete 2")

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ideas:
        await update.message.reply_text("Немає ідей для перевірки.")
        return

    text = "\n\n".join([
        f"#{i+1} {idea['user']} ({idea['user_id']})\n{idea['text']}\n{idea['time']}"
        for i, idea in enumerate(ideas)
    ])
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Доступні команди:\n"
        "/start — почати роботу з ботом\n"
        "/ideas — показати всі ідеї\n"
        "/review — переглянути ідеї з авторами\n"
        "/delete <номер> — видалити ідею (адмінам)\n"
        "/help — показати це меню"
    )

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не знайдено в Environment!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ideas", show_ideas))
    app.add_handler(CommandHandler("delete", delete_idea))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    if os.getenv("RENDER"):
        WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")
        PORT = int(os.getenv("PORT", "10000"))
        if not WEBHOOK_URL:
            logger.error("❌ WEBHOOK_URL не знайдено! Для Render потрібно, щоб воно було у RENDER_EXTERNAL_URL.")
            exit(1)
        logger.info("🚀 Запуск через webhook на Render")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        logger.info("✅ Запуск локально через polling")
        app.run_polling()
