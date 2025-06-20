import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token and private channel ID
BOT_TOKEN = '7462406196:AAFXdCHylU-JGT8QzymI7vrN0-if-Z3dbjg'
CHANNEL_ID = '-1001943585227'  # Private channel ID

# Function to handle incoming files
def handle_file(update: Update, context):
    # Check if the message contains a document (like .pdf, .doc, .zip, etc.)
    if update.message.document:
        file = update.message.document
    # Check if the message contains an image
    elif update.message.photo:
        file = update.message.photo[-1]  # Take the highest quality image
    # Check if the message contains a video or audio file
    elif update.message.video or update.message.audio:
        file = update.message.video if update.message.video else update.message.audio
    else:
        update.message.reply_text("Please send a valid file (document, image, video, or audio).")
        return

    try:
        # Forward the file to the private channel
        sent_message = context.bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
        
        # Get the file ID from the forwarded message
        if sent_message.document:
            file_id = sent_message.document.file_id
        elif sent_message.photo:
            file_id = sent_message.photo[-1].file_id
        elif sent_message.video:
            file_id = sent_message.video.file_id
        elif sent_message.audio:
            file_id = sent_message.audio.file_id

        # Use bot.getFile to retrieve the direct download link for the file
        file_info = context.bot.get_file(file_id)
        download_link = file_info.file_path  # This is the direct link to download the file
        
        # Send the download link back to the user
        update.message.reply_text(f"File stored successfully! Here is your download link: {download_link}")

    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")
        logger.error(f"Error handling file: {e}")

# Function to handle '/start' command
def start(update: Update, context):
    update.message.reply_text("Welcome! Send me any file (PDF, DOC, ZIP, image, video, or audio), and I'll generate a download link for you.")

# Error handling function
def error(update: Update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    # Initialize the bot with the token
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add a handler for the '/start' command
    dispatcher.add_handler(CommandHandler('start', start))

    # Add a handler for receiving files (documents, images, videos, etc.)
    dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video | Filters.audio, handle_file))

    # Log all errors
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Keep the bot running until interrupted
    updater.idle()

if __name__ == '__main__':
    main()