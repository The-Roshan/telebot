import os
import logging
import redis
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_CHANNEL_ID = os.getenv('DB_CHANNEL_ID')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

if not all([BOT_TOKEN, DB_CHANNEL_ID, ADMIN_IDS]):
    raise ValueError("Missing required environment variables")

bot = Bot(token=BOT_TOKEN)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

TASKS = {}  # {task_id: {description, due_date, assigned_to, status}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Add Task", callback_data="add_task")],
        [InlineKeyboardButton("List Tasks", callback_data="list_tasks")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Task Manager Bot!\nManage your tasks efficiently.",
        reply_markup=reply_markup
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter: /add_task <description> <due_date> (e.g., /add_task Finish report 2025-12-01)")

async def handle_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add_task <description> <due_date>")
        return
    description = ' '.join(args[:-1])
    due_date = args[-1]
    try:
        datetime.strptime(due_date, '%Y-%m-%d')
        task_id = len(TASKS) + 1
        TASKS[task_id] = {"description": description, "due_date": due_date, "assigned_to": chat_id, "status": "pending"}
        await bot.send_message(
            chat_id=DB_CHANNEL_ID,
            text=f"Task: {description} due {due_date} by user {chat_id}"
        )
        redis_client.set(f"task_reminder_{task_id}", chat_id)
        await update.message.reply_text(f"Added task: {description} due {due_date}")
    except ValueError:
        await update.message.reply_text("Invalid date format. Use YYYY-MM-DD.")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_tasks = [t for t in TASKS.values() if t['assigned_to'] == chat_id]
    if not user_tasks:
        await update.message.reply_text("No tasks assigned.")
        return
    response = "Your Tasks:\n"
    for tid, task in TASKS.items():
        if task['assigned_to'] == chat_id:
            response += f"ID: {tid}, Desc: {task['description']}, Due: {task['due_date']}, Status: {task['status']}\n"
    await update.message.reply_text(response)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /done <task_id>")
        return
    try:
        task_id = int(args[0])
        if task_id in TASKS and TASKS[task_id]['assigned_to'] == chat_id:
            TASKS[task_id]['status'] = 'done'
            redis_client.delete(f"task_reminder_{task_id}")
            await update.message.reply_text(f"Task {task_id} marked as done.")
        else:
            await update.message.reply_text("Invalid task ID.")
    except ValueError:
        await update.message.reply_text("Invalid task ID.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "add_task":
        await query.message.reply_text("Enter: /add_task <description> <due_date>")
    elif data == "list_tasks":
        chat_id = query.message.chat_id
        user_tasks = [t for t in TASKS.values() if t['assigned_to'] == chat_id]
        response = "Your Tasks:\n" if user_tasks else "No tasks assigned."
        for tid, task in TASKS.items():
            if task['assigned_to'] == chat_id:
                response += f"ID: {tid}, Desc: {task['description']}, Due: {task['due_date']}, Status: {task['status']}\n"
        await query.message.reply_text(response)
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_task", handle_add_task))
    application.add_handler(CommandHandler("list_tasks", list_tasks))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()