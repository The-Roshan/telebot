import os
import json
import logging
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

EVENTS = {}  # {event_id: {name, date, creator_id, rsvps}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Create Event", callback_data="create_event")],
        [InlineKeyboardButton("List Events", callback_data="list_events")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Event Scheduler Bot!\nOrganize events and polls easily.",
        reply_markup=reply_markup
    )

async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter: /create_event <name> <date> (e.g., /create_event Meeting 2025-12-01)")

async def handle_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /create_event <name> <date>")
        return
    name = ' '.join(args[:-1])
    date = args[-1]
    try:
        datetime.strptime(date, '%Y-%m-%d')
        event_id = len(EVENTS) + 1
        EVENTS[event_id] = {"name": name, "date": date, "creator_id": chat_id, "rsvps": []}
        await bot.send_message(
            chat_id=DB_CHANNEL_ID,
            text=f"Event: {name} on {date} by user {chat_id}"
        )
        keyboard = [[InlineKeyboardButton("RSVP", callback_data=f"rsvp_{event_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Event created: {name} on {date}", reply_markup=reply_markup)
    except ValueError:
        await update.message.reply_text("Invalid date format. Use YYYY-MM-DD.")

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not EVENTS:
        await update.message.reply_text("No events scheduled.")
        return
    response = "Scheduled Events:\n"
    for eid, event in EVENTS.items():
        response += f"ID: {eid}, Name: {event['name']}, Date: {event['date']}, RSVPs: {len(event['rsvps'])}\n"
    await update.message.reply_text(response)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    if data == "create_event":
        await query.message.reply_text("Enter: /create_event <name> <date>")
    elif data == "list_events":
        response = "Scheduled Events:\n" if EVENTS else "No events scheduled."
        for eid, event in EVENTS.items():
            response += f"ID: {eid}, Name: {event['name']}, Date: {event['date']}, RSVPs: {len(event['rsvps'])}\n"
        await query.message.reply_text(response)
    elif data.startswith("rsvp_"):
        event_id = int(data.split("_")[1])
        if event_id in EVENTS and chat_id not in EVENTS[event_id]["rsvps"]:
            EVENTS[event_id]["rsvps"].append(chat_id)
            await query.message.reply_text(f"RSVP confirmed for {EVENTS[event_id]['name']}!")
        else:
            await query.message.reply_text("Already RSVP'd or invalid event.")
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create_event", handle_create_event))
    application.add_handler(CommandHandler("list_events", list_events))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()