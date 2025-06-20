import os
import json
import logging
import pytesseract
from PIL import Image
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_CHANNEL_ID = os.getenv('DB_CHANNEL_ID')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

if not all([BOT_TOKEN, DB_CHANNEL_ID, ADMIN_IDS]):
    raise ValueError("Missing required environment variables")

# Initialize bot
bot = Bot(token=BOT_TOKEN)

# In-memory storage for user data
USER_TRANSACTIONS = {}  # {user_id: [{amount, category, type, date}]}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Add Expense", callback_data="add_expense")],
        [InlineKeyboardButton("Add Income", callback_data="add_income")],
        [InlineKeyboardButton("View Stats", callback_data="view_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Finance Tracker Bot!\nTrack your expenses and income easily.",
        reply_markup=reply_markup
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter expense: /add_expense <amount> <category> (e.g., /add_expense 50 Food)")

async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter income: /add_income <amount> <source> (e.g., /add_income 1000 Salary)")

async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add_expense <amount> <category>")
        return
    try:
        amount = float(args[0])
        category = ' '.join(args[1:])
        transaction = {"amount": amount, "category": category, "type": "expense", "date": datetime.utcnow().isoformat()}
        USER_TRANSACTIONS.setdefault(chat_id, []).append(transaction)
        await bot.send_message(
            chat_id=DB_CHANNEL_ID,
            text=f"Expense: {amount} {category} by user {chat_id}"
        )
        await update.message.reply_text(f"Added expense: {amount} for {category}")
    except ValueError:
        await update.message.reply_text("Invalid amount. Use numbers only.")

async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add_income <amount> <source>")
        return
    try:
        amount = float(args[0])
        source = ' '.join(args[1:])
        transaction = {"amount": amount, "source": source, "type": "income", "date": datetime.utcnow().isoformat()}
        USER_TRANSACTIONS.setdefault(chat_id, []).append(transaction)
        await bot.send_message(
            chat_id=DB_CHANNEL_ID,
            text=f"Income: {amount} {source} by user {chat_id}"
        )
        await update.message.reply_text(f"Added income: {amount} from {source}")
    except ValueError:
        await update.message.reply_text("Invalid amount. Use numbers only.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    transactions = USER_TRANSACTIONS.get(chat_id, [])
    if not transactions:
        await update.message.reply_text("No transactions found.")
        return
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    await update.message.reply_text(
        f"Stats:\nTotal Income: {total_income}\nTotal Expenses: {total_expense}\nBalance: {total_income - total_expense}"
    )

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not update.message.photo:
        await update.message.reply_text("Please send a receipt image.")
        return
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_data = await file.download_as_bytearray()
        image = Image.open(BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        # Simple extraction (assumes amount is a number)
        amounts = [float(x) for x in text.split() if x.replace('.', '', 1).isdigit()]
        if amounts:
            amount = max(amounts)  # Assume largest number is the total
            transaction = {"amount": amount, "category": "Receipt", "type": "expense", "date": datetime.utcnow().isoformat()}
            USER_TRANSACTIONS.setdefault(chat_id, []).append(transaction)
            await bot.send_photo(chat_id=DB_CHANNEL_ID, photo=photo.file_id, caption=f"Receipt by user {chat_id}")
            await update.message.reply_text(f"Added expense from receipt: {amount}")
        else:
            await update.message.reply_text("Could not extract amount from receipt.")
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        await update.message.reply_text("Error processing receipt.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "add_expense":
        await query.message.reply_text("Enter: /add_expense <amount> <category>")
    elif data == "add_income":
        await query.message.reply_text("Enter: /add_income <amount> <source>")
    elif data == "view_stats":
        chat_id = query.message.chat_id
        transactions = USER_TRANSACTIONS.get(chat_id, [])
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        await query.message.reply_text(
            f"Stats:\nTotal Income: {total_income}\nTotal Expenses: {total_expense}\nBalance: {total_income - total_expense}"
        )
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_expense", handle_expense))
    application.add_handler(CommandHandler("add_income", handle_income))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()