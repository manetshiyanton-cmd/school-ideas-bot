import os
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === ФАЙЛ З ІДЕЯМИ ===
IDEAS_FILE = "ideas.json"

# === ФУНКЦІЇ ДЛЯ РОБОТИ З ІДЕЯМИ ===
def load_ideas():
    if os.path.exists(IDEAS_FILE):
        try:
            with open(IDEAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_ideas(ideas):
    with open(IDEAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)

# === КОМАНДИ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли ідею — я її збережу. Щоб переглянути, пиши /ideas.")

async def add_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idea = update.message.text.strip()
    ideas = load_ideas()
    ideas.append({"text": idea, "user": update.effective_user.first_name})
    save_ideas(ideas)
    await update.message.reply_text("✅ Ідею додано!")

async def list_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ideas = load_ideas()
    if not ideas:
        await update.message.reply_text("📭 Немає жодної ідеї.")
    else:
        text = "\n\n".join([f"{i+1}. {idea['text']} — від {idea['user']}" for i, idea in enumerate(ideas)])
        await update.message.reply_text(f"💡 Ідеї:\n\n{text}\n\nЩоб видалити ідею, напиши /delete <номер>")

async def delete_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ideas = load_ideas()
    if not ideas:
        await update.message.reply_text("😕 Немає ідей для видалення.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Вкажи номер ідеї, яку хочеш видалити. Наприклад: /delete 2")
        return

    try:
        num = int(context.args[0]) - 1
        if num < 0 or num >= len(ideas):
            await update.message.reply_text("❌ Такої ідеї не існує.")
            return

        deleted_idea = ideas.pop(num)
        save_ideas(ideas)
        await update.message.reply_text(f"🗑 Ідею '{deleted_idea['text']}' видалено!")
    except ValueError:
        await update.message.reply_text("⚠️ Вкажи правильний номер!")

# === ГОЛОВНА ФУНКЦІЯ ===
async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не знайдено в Environment!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ideas", list_ideas))
    app.add_handler(CommandHandler("delete", delete_idea))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_idea))

    logger.info("✅ Бот запущено локально (polling)...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
