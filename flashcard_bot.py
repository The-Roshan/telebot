import os
import json
import logging
import random
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

DECKS = {}  # {user_id: {deck_name: [{question, answer}]}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Add Card", callback_data="add_card")],
        [InlineKeyboardButton("Start Quiz", callback_data="start_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Flashcard Bot!\nStudy smarter with digital flashcards.",
        reply_markup=reply_markup
    )

async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter: /add_card <deck_name> <question> <answer>")

async def handle_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /add_card <deck_name> <question> <answer>")
        return
    deck_name = args[0]
    question = args[1]
    answer = ' '.join(args[2:])
    DECKS.setdefault(chat_id, {}).setdefault(deck_name, []).append({"question": question, "answer": answer})
    await bot.send_message(
        chat_id=DB_CHANNEL_ID,
        text=f"Card: {question} -> {answer} in deck {deck_name} by user {chat_id}"
    )
    await update.message.reply_text(f"Added card to deck {deck_name}")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /quiz <deck_name>")
        return
    deck_name = args[0]
    if chat_id not in DECKS or deck_name not in DECKS[chat_id]:
        await update.message.reply_text("Deck not found.")
        return
    card = random.choice(DECKS[chat_id][deck_name])
    keyboard = [[InlineKeyboardButton("Show Answer", callback_data=f"show_answer_{card['answer']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Question: {card['question']}", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "add_card":
        await query.message.reply_text("Enter: /add_card <deck_name> <question> <answer>")
    elif data == "start_quiz":
        await query.message.reply_text("Enter: /quiz <deck_name>")
    elif data.startswith("show_answer_"):
        answer = data.replace("show_answer_", "")
        await query.message.reply_text(f"Answer: {answer}")
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_card", handle_add_card))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()