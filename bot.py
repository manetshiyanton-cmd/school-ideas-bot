import logging
import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === НАЛАШТУВАННЯ ===
TOKEN = os.getenv("BOT_TOKEN", "8277763753:AAFsw4MaJ6mRa7P6zIZMVZWYeA8WcWjhO7I")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6429865341"))  # ✅ зчитує з Environment або fallback
WEBHOOK_URL = "https://school-ideas-bot-6.onrender.com/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ideas = {}
next_id = 1


# === КОМАНДИ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Надішли свою ідею для школи — ми її збережемо.\n"
        "Щоб побачити всі команди, напиши /help."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команди:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "Просто напиши свою ідею — ми її збережемо.\n"
        "/review — перегляд усіх ідей (адмін)\n"
        "/reply <id> <текст> — відповісти на ідею (адмін)\n"
        "/delete <id> — видалити ідею (адмін)"
    )


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(f"⛔ Немає доступу. Твій ID: {user_id}")
        return

    if not ideas:
        await update.message.reply_text("💤 Немає ідей.")
        return

    response = "\n\n".join([f"🆔 {i}: {t}" for i, t in ideas.items()])
    await update.message.reply_text(f"💡 Ідеї:\n\n{response}")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(f"⛔ Немає доступу. Твій ID: {user_id}")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Використання: /reply <id> <текст>")
        return

    idea_id = int(context.args[0])
    reply_text = " ".join(context.args[1:])

    if idea_id not in ideas:
        await update.message.reply_text("❌ Ідеї з таким ID немає.")
        return

    await update.message.reply_text(f"✅ Відповідь на ідею #{idea_id}: {reply_text}")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(f"⛔ Немає доступу. Твій ID: {user_id}")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Використання: /delete <id>")
        return

    idea_id = int(context.args[0])

    if idea_id not in ideas:
        await update.message.reply_text("❌ Ідеї з таким ID не існує.")
        return

    del ideas[idea_id]
    await update.message.reply_text(f"🗑️ Ідею #{idea_id} видалено.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global next_id
    text = update.message.text.strip()

    ideas[next_id] = text
    await update.message.reply_text(f"✅ Ідею збережено під номером {next_id}!")
    next_id += 1


# === ОСНОВНИЙ ЦИКЛ ===
async def main():
    logger.info(f"🌐 Налаштовую вебхук: {WEBHOOK_URL}")
    logger.info(f"👑 ADMIN_ID = {ADMIN_ID}")

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("review", review))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
