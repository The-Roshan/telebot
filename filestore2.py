import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace these with your actual bot token and channel chat ID
BOT_TOKEN = ''
CHANNEL_ID = ''  # Private channel ID

# Dictionary to store file_id for each user session
file_storage = {}

# Function to handle /start command with a file ID
def start(update: Update, context: CallbackContext):
    args = context.args

    # Check if the start command includes a file_id
    if args:
        file_id = args[0]
        if file_id in file_storage:
            file_info = file_storage[file_id]
            file_type = file_info['type']

            # Send the file based on its type
            if file_type == 'document':
                context.bot.send_document(chat_id=update.message.chat_id, document=file_info['file_id'])
            elif file_type == 'photo':
                context.bot.send_photo(chat_id=update.message.chat_id, photo=file_info['file_id'])
            elif file_type == 'video':
                context.bot.send_video(chat_id=update.message.chat_id, video=file_info['file_id'])
            elif file_type == 'audio':
                context.bot.send_audio(chat_id=update.message.chat_id, audio=file_info['file_id'])

            update.message.reply_text("Here is your file!")
        else:
            update.message.reply_text("Invalid file request.")
    else:
        update.message.reply_text("Welcome! Please send a file to generate a shareable link.")

# Function to handle incoming files
def handle_file(update: Update, context: CallbackContext):
    file = None
    file_type = None

    # Detect file type and get file ID
    if update.message.document:
        file = update.message.document
        file_type = 'document'
    elif update.message.photo:
        file = update.message.photo[-1]
        file_type = 'photo'
    elif update.message.video:
        file = update.message.video
        file_type = 'video'
    elif update.message.audio:
        file = update.message.audio
        file_type = 'audio'
    else:
        update.message.reply_text("Please send a valid file (document, image, video, or audio).")
        return

    # Store the file in the private channel
    try:
        sent_message = context.bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)

        # Get file_id from the forwarded message
        if sent_message.document:
            file_id = sent_message.document.file_id
        elif sent_message.photo:
            file_id = sent_message.photo[-1].file_id
        elif sent_message.video:
            file_id = sent_message.video.file_id
        elif sent_message.audio:
            file_id = sent_message.audio.file_id

        # Generate a unique link for the user to access the file later
        file_key = f"{update.message.chat_id}_{file.file_unique_id}"
        file_storage[file_key] = {'file_id': file_id, 'type': file_type}

        # Generate the bot deep link
        bot_link = f"https://t.me/{context.bot.username}?start={file_key}"

        # Send the deep link to the user
        update.message.reply_text(f"File stored successfully! Click here to get the file: {bot_link}")

    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")
        logger.error(f"Error handling file: {e}")

# Error handling function
def error(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    # Initialize the bot with the token
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add a handler for the /start command with arguments
    dispatcher.add_handler(CommandHandler('start', start))

    # Add a handler for receiving files
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video | Filters.audio, handle_file))

    # Log all errors
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Keep the bot running until interrupted
    updater.idle()

if __name__ == '__main__':
    main()
