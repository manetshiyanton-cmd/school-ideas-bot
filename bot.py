import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# 🔹 Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔹 Конфіг
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [6505686873]  # заміни на свій Telegram ID
IDEAS_FILE = "ideas.json"

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не знайдено в Environment!")
    raise SystemExit

# 🔹 Завантаження/збереження ідей
def load_ideas():
    if os.path.exists(IDEAS_FILE):
        with open(IDEAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_ideas(ideas):
    with open(IDEAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)

# 🔹 Команди
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли ідею або подивись список — /ideas")

async def add_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Напиши свою ідею після /add або просто повідомленням.")
        return

    ideas = load_ideas()
    ideas.append({"user": update.effective_user.first_name, "text": text})
    save_ideas(ideas)

    await update.message.reply_text("✅ Ідею додано!")

async def show_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ideas = load_ideas()
    if not ideas:
        await update.message.reply_text("📭 Ідей поки немає.")
        return

    text = "💡 Список ідей:\n\n"
    for i, idea in enumerate(ideas, start=1):
        text += f"{i}. {idea['text']} — {idea['user']}\n"

    # Якщо адмін — додаємо кнопки
    if update.effective_user.id in ADMIN_IDS:
        buttons = [
            [InlineKeyboardButton(f"❌ Видалити {i+1}", callback_data=f"delete_{i}")]
            for i in range(len(ideas))
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text)

# 🔹 Обробка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("delete_"):
        return

    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("🚫 У тебе немає прав для видалення ідей.")
        return

    index = int(query.data.split("_")[1])
    ideas = load_ideas()

    if 0 <= index < len(ideas):
        deleted = ideas.pop(index)
        save_ideas(ideas)
        await query.edit_message_text(f"🗑 Ідею видалено:\n{deleted['text']}")
    else:
        await query.edit_message_text("⚠️ Ідею не знайдено або вже видалено.")

# 🔹 Запуск
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ideas", show_ideas))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_idea))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("✅ Бот запущено (polling)...")

    # 🔧 Фікс для Render (використовує вже існуючий event loop)
    try:
        asyncio.get_event_loop().run_until_complete(app.run_polling())
    except RuntimeError:
        asyncio.run(app.run_polling())

if __name__ == "__main__":
    run_bot()
