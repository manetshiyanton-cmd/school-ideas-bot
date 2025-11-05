import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ===== Налаштування логів =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

# ===== Адміни =====
ADMINS = [123456789]  # 🔹 ВСТАВ СВІЙ TELEGRAM ID

# ===== Сховище ідей =====
ideas = []

# ===== Команди =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Надішли свою ідею, і я її збережу!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 Команди:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "/review — перегляд усіх ідей (адмін)\n"
        "/reply <id> <текст> — відповісти на ідею (адмін)\n"
        "/delete <id> — видалити ідею (адмін)\n"
        "\nПросто напиши свою ідею — і я її збережу 💡"
    )
    await update.message.reply_text(text)

# ===== Збереження ідей =====
async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ Введи ідею текстом.")
        return
    idea_id = len(ideas) + 1
    ideas.append({"id": idea_id, "text": text, "user": update.message.from_user.full_name})
    await update.message.reply_text(f"✅ Ідею #{idea_id} збережено!")

# ===== Перегляд ідей =====
async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Ти не маєш прав переглядати всі ідеї.")
        return

    if not ideas:
        await update.message.reply_text("😕 Ще немає жодної ідеї.")
        return

    text = "💡 Список ідей:\n"
    for idea in ideas:
        text += f"#{idea['id']}: {idea['text']} — від {idea['user']}\n"
    await update.message.reply_text(text)

# ===== Видалення ідей =====
async def delete_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Ти не маєш прав для цієї дії.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Вкажи ID ідеї для видалення, наприклад: /delete 2")
        return

    try:
        idea_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ ID має бути числом.")
        return

    for idea in ideas:
        if idea["id"] == idea_id:
            ideas.remove(idea)
            await update.message.reply_text(f"🗑 Ідею #{idea_id} видалено.")
            return

    await update.message.reply_text("❌ Ідею з таким ID не знайдено.")

# ===== Обробка кнопок (плейсхолдер) =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔘 Кнопка натиснута!")

# ===== Основний запуск =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("review", review))
app.add_handler(CommandHandler("delete", delete_idea))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))
app.add_handler(CallbackQueryHandler(button_handler))

# ===== Webhook для Render =====
if WEBHOOK_URL:
    port = int(os.environ.get("PORT", 10000))
    webhook_url = f"{WEBHOOK_URL}/webhook"

    async def main():
        logger.info(f"🌐 Налаштовую вебхук: {webhook_url}")
        await app.bot.set_webhook(webhook_url)
        await app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=webhook_url,
        )
else:
    async def main():
        logger.info("🚀 Запуск у режимі polling (локально)")
        await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
