# school_ideas_bot.py
import logging
import sqlite3
from datetime import datetime
import os
from typing import List

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

TOKEN = "8277763753:AAFsw4MaJ6mRa7P6zIZMVZWYeA8WcWjhO7I"  # 🔹 сюди встав свій токен з BotFather

# 🔸 Вкажи сюди свої Telegram ID, через кому якщо кілька (наприклад: [123456789, 987654321])
ADMIN_IDS: List[int] = [1407696674,955785809]  

DB_PATH = "ideas.db"
START_MESSAGE = "💬 Привіт! Поділись ідеєю, як зробити школу кращою — самоврядування все побачить 😉"

# ----------------------------------
# Логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- БАЗА ДАНИХ ----------
def init_db(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            text TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_idea(user_id: int, username: str, first_name: str, text: str, path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ideas (user_id, username, first_name, text, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, text, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def fetch_all_ideas(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, username, first_name, text, created_at FROM ideas ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- HANDLER-И ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Відправляє коротке привітання і підказку."""
    await update.message.reply_text(START_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "Команди:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "Просто надішли своє повідомлення тут — це буде збережено як ідея.\n"
        "/review — (тільки для адміністраторів) перегляд усіх ідей"
    )
    await update.message.reply_text(txt)


async def receive_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка звичайного текстового повідомлення — вважаємо його ідеєю."""
    msg = update.message
    user = msg.from_user
    text = msg.text.strip()
    if not text:
        await msg.reply_text("Порожня ідея? Напиши, будь ласка, коротко свою пропозицію.")
        return

    # Збереження
    save_idea(user.id, user.username or "", user.first_name or "", text)
    print(f"💡 Отримано ідею від @{user.username}: {text}")
    await msg.reply_text("Дякуємо! Ідея отримана — ми її розглянемо. 🙏")


async def review_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати список ідей — доступно лише адміністраторам (вказаним у ADMIN_IDS)."""
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("У тебе немає доступу до цієї команди.")
        return

    rows = fetch_all_ideas()
    if not rows:
        await update.message.reply_text("Ідей поки що немає.")
        return

    # Формуємо відповідь — лімітуємо кількість символів, щоб не перевантажити повідомлення
    messages = []
    for r in rows[:50]:  # максимум 50 останніх
        iid, uid, username, first_name, text, created_at = r
        created = created_at.replace("T", " ")[:19]
        name = f"@{username}" if username else (first_name or "Учень")
        preview = text if len(text) <= 250 else text[:247] + "..."
        messages.append(f"#{iid} {name} ({uid})\n{preview}\n{created}")

    CHUNK = "\n\n---\n\n"
    payload = CHUNK.join(messages)
    MAX_LEN = 3900
    if len(payload) <= MAX_LEN:
        await update.message.reply_text(payload)
    else:
        parts = []
        cur = []
        cur_len = 0
        for m in messages:
            if cur_len + len(m) + len(CHUNK) > MAX_LEN:
                parts.append(CHUNK.join(cur))
                cur = [m]
                cur_len = len(m)
            else:
                cur.append(m)
                cur_len += len(m) + len(CHUNK)
        if cur:
            parts.append(CHUNK.join(cur))
        for p in parts:
            await update.message.reply_text(p)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не впевнений, що ти хотів цим сказати. Просто напиши свою ідею — ми збережемо її.")


# ---------- MAIN ----------
def main():
    init_db(DB_PATH)
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Встав свій BotFather TOKEN у файл перед запуском.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("review", review_ideas))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_idea))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("✅ Бот запущений і слухає повідомлення...")
    logger.info("Бот запущено. Очікування повідомлень...")
    app.run_polling()


if __name__ == "__main__":
    main()
