from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# список адмінів (вкажи свої ID)
ADMINS = [123456789, 987654321]

ideas = []  # тут зберігаються ідеї

# команда /delete
async def delete_idea(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 Тільки адміни можуть видаляти ідеї.")
        return

    if not ideas:
        await update.message.reply_text("💡 Немає ідей для видалення.")
        return

    # створюємо кнопки для кожної ідеї
    keyboard = []
    for i, idea in enumerate(ideas):
        keyboard.append([InlineKeyboardButton(f"❌ {idea}", callback_data=f"delete_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вибери ідею для видалення:", reply_markup=reply_markup)

# обробник натискання кнопки
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in ADMINS:
        await query.edit_message_text("🚫 У тебе немає прав видаляти ідеї.")
        return

    try:
        if query.data.startswith("delete_"):
            index = int(query.data.split("_")[1])
            if 0 <= index < len(ideas):
                deleted_idea = ideas.pop(index)
                await query.edit_message_text(f"🗑 Ідею видалено: «{deleted_idea}»")
            else:
                await query.edit_message_text("❌ Ідею не знайдено.")
    except Exception as e:
        await query.edit_message_text(f"⚠️ Помилка при видаленні: {e}")
