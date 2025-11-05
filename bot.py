import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Налаштування логів
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    logger.error("❌ BOT_TOKEN не знайдено в Environment!")
    raise SystemExit

# Створюємо застосунок
app = ApplicationBuilder().token(TOKEN).build()

# Проста команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привіт! Бот на Render працює через webhook ✅")

app.add_handler(CommandHandler("start", start))

# Обробка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Натиснуто кнопку!")

app.add_handler(CallbackQueryHandler(button_handler))

# === Вебхук режим для Render ===
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
    # fallback — якщо локально
    async def main():
        logger.info("🚀 Запуск у режимі polling (локально)")
        await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
