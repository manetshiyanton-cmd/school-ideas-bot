import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# === Налаштування логів ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Змінні середовища ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не знайдено в Environment!")
    exit(1)

# === Список ідей ===
ideas = []

# === ID адмінів (вкажи свої ID сюди) ===
ADMINS = [123456789, 987654321]  # заміни своїми Telegram ID

# === Команди ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Вітаю! Надішли мені свою ідею 💡")

async def add_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return
    ideas.append(text)
    await update.message.reply_text("✅ Ідею збережено!")

async def list_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ideas:
        await update.message.reply_text("📭 Поки що ідей немає.")
        return

    message = "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])
    await update.message.reply_text(f"💡 Ідеї:\n{message}")

# === Видалення ідей (лише адміни) ===
async def delete_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Ти не маєш прав для видалення ідей.")
        return

    if not ideas:
        await update.message.reply_text("😕 Немає ідей для видалення.")
        return

    keyboard = [
        [InlineKeyboardButton(f"❌ {idea}", callback_data=f"delete_{i}")]
        for i, idea in enumerate(ideas)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вибери ідею для видалення:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("delete_"):
        index = int(query.data.split("_")[1])
        if 0 <= index < len(ideas):
            deleted_idea = ideas.pop(index)
            await query.edit_message_text(f"🗑 Ідею видалено:\n«{deleted_idea}»")
        else:
            await query.edit_message_text("⚠️ Ідея не знайдена або вже видалена.")

# === Основна функція ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_ideas))
    app.add_handler(CommandHandler("deleteidea", delete_idea))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_idea))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("✅ Бот запущено (polling)...")
    app.run_polling()

# === Запуск ===
if __name__ == "__main__":
    main()
