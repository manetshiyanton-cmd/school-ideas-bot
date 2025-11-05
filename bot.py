import os
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

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

# === ID адміністратора ===
ADMIN_ID = 6429865341  # заміни на свій Telegram ID

# === КОМАНДИ БОТА ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли мені свою ідею, і я її збережу!")

async def show_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ideas:
        await update.message.reply_text("Поки що немає жодної ідеї 😢")
    else:
        text = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(ideas))
        await update.message.reply_text(f"💡 Ідеї:\n{text}")

async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text:
        ideas.append(text)
        save_ideas(ideas)
        await update.message.reply_text("✅ Ідею збережено!")
    else:
        await update.message.reply_text("Будь ласка, напиши ідею текстом 😉")

# === Команда для адміна — видалення ідеї ===
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Ти не маєш доступу до цього.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Використання: /delete <номер ідеї>")
        return

    try:
        idea_index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("⚠️ Номер має бути числом.")
        return

    if 0 <= idea_index < len(ideas):
        removed = ideas.pop(idea_index)
        save_ideas(ideas)
        await update.message.reply_text(f"🗑️ Ідею видалено: {removed}")
    else:
        await update.message.reply_text("❌ Ідеї з таким номером немає.")

# === Команда для адміна — перегляд усіх ідей ===
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Ти не маєш доступу до цього.")
        return

    if not ideas:
        await update.message.reply_text("💤 Поки що немає жодної ідеї.")
        return

    text = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(ideas))
    await update.message.reply_text(f"💡 Всі ідеї:\n{text}")

# === ЗАПУСК БОТА ===
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не знайдено в Environment!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ideas", show_ideas))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("review", review))
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
