import os
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Для Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === ШЛЯХ ДО ФАЙЛУ ІДЕЙ ===
IDEAS_FILE = "ideas.json"

# === ФУНКЦІЇ ДЛЯ ЗБЕРЕЖЕННЯ ІДЕЙ ===
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

# === GOOGLE SHEETS НАЛАШТУВАННЯ ===
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_SERVICE_JSON = os.getenv("GOOGLE_SERVICE_JSON")

gc = None
worksheet = None

try:
    creds_dict = json.loads(GOOGLE_SERVICE_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SHEET_ID).sheet1
    logger.info("✅ Підключення до Google Sheets успішне")
except Exception as e:
    logger.error(f"❌ Помилка підключення до Google Sheets: {e}")

# === КОМАНДИ БОТА ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли мені свою ідею, і я її збережу!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команди:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "/ideas — переглянути всі ідеї\n"
        "/delete <номер> — видалити ідею (адмін)\n"
        "Просто напиши свою ідею — ми її збережемо."
    )

async def show_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ideas:
        await update.message.reply_text("Поки що немає жодної ідеї 😢")
    else:
        text = ""
        for i, idea in enumerate(ideas):
            user = idea.get("user", "Unknown")
            user_id = idea.get("user_id", "Unknown")
            idea_text = idea.get("text", "")
            timestamp = idea.get("time", "")
            text += f"#{i+1} @{user} ({user_id})\n{idea_text}\n{timestamp}\n\n"
        await update.message.reply_text(f"💡 Ідеї:\n{text.strip()}")

async def delete_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_]
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Ти не маєш доступу до цього.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Використання: /delete <номер>")
        return

    idx = int(context.args[0]) - 1
    if idx < 0 or idx >= len(ideas):
        await update.message.reply_text("❌ Ідеї з таким номером немає.")
        return

    removed = ideas.pop(idx)
    save_ideas(ideas)
    await update.message.reply_text(f"🗑️ Ідею #{idx+1} видалено.")

# === ОБРОБКА ПОВІДОМЛЕНЬ ===
async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text:
        idea_entry = {
            "user": update.effective_user.username or update.effective_user.full_name,
            "user_id": update.effective_user.id,
            "text": text,
            "time": str(update.message.date)
        }
        ideas.append(idea_entry)
        save_ideas(ideas)
        await update.message.reply_text("✅ Ідею збережено!")

        # Запис у Google Sheets
        if worksheet:
            try:
                worksheet.append_row([
                    idea_entry["user"],
                    idea_entry["user_id"],
                    idea_entry["text"],
                    idea_entry["time"]
                ])
            except Exception as e:
                logger.error(f"❌ Не вдалося додати в Google Sheets: {e}")
    else:
        await update.message.reply_text("Будь ласка, напиши ідею текстом 😉")

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не знайдено в Environment!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ideas", show_ideas))
    app.add_handler(CommandHandler("delete", delete_idea))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    # Якщо Render середовище — запускаємо через webhook
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
