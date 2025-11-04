import os
import logging
import sqlite3
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ---------- НАЛАШТУВАННЯ ----------
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

DB_PATH = "ideas.db"
START_MESSAGE = "💬 Привіт! Поділись ідеєю, як зробити школу кращою — самоврядування все побачить 😉"

# ---------- ЛОГУВАННЯ ----------
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

def get_idea_by_id(idea_id: int, path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM ideas WHERE id = ?", (idea_id,))
    row = cur.fetchone()
    conn.close()
    return row

# ---------- КОМАНДИ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "Команди:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "Просто напиши свою ідею — ми її збережемо.\n"
        "/review — перегляд усіх ідей (адмін)\n"
        "/reply <id> <текст> — відповісти на ідею (адмін)"
    )
    await update.message.reply_text(txt)

async def receive_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user
    text = msg.text.strip()
    if not text:
        await msg.reply_text("Порожня ідея? Напиши коротко, що саме ти пропонуєш 🙏")
        return
    save_idea(user.id, user.username or "", user.first_name or "", text)
    await msg.reply_text("Дякуємо! Ідея отримана — самоврядування її перегляне 💡")

async def review_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("У тебе немає доступу до цієї команди.")
        return

    rows = fetch_all_ideas()
    if not rows:
        await update.message.reply_text("Ідей поки що немає.")
        return

    messages = []
    for r in rows[:50]:
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

async def reply_to_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Ця команда тільки для адміністраторів 🚫")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Використання: /reply <id> <текст відповіді>")
        return

    try:
        idea_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID має бути числом.")
        return

    idea_row = get_idea_by_id(idea_id)
    if not idea_row:
        await update.message.reply_text("Ідею з таким ID не знайдено.")
        return

    target_user_id = idea_row[0]
    reply_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📢 Відповідь на твою ідею #{idea_id}:\n\n{reply_text}"
        )
        await update.message.reply_text("✅ Відповідь відправлено користувачу.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Не вдалося відправити: {e}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не впевнений, що ти хотів цим сказати 😅 Просто напиши свою ідею.")

# ---------- MAIN ----------
if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ Не знайдено BOT_TOKEN у Environment Variables!")
        exit(1)

    init_db(DB_PATH)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("review", review_ideas))
    app.add_handler(CommandHandler("reply", reply_to_idea))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_idea))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # ---------- WEBHOOK SETUP ----------
    PORT = int(os.environ.get("PORT", 5000))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # додай через Render → Environment

    if not WEBHOOK_URL:
        logger.error("❌ Не знайдено WEBHOOK_URL у Environment Variables!")
        exit(1)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN
    )
    app.bot.set_webhook(f"{WEBHOOK_URL}{TOKEN}")

    logger.info("✅ Бот запущено через WEBHOOK. Очікування повідомлень...")
