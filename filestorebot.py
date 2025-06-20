import os
import requests
import json
from datetime import datetime, timedelta
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError
import logging
import urllib.parse
import re

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_CHANNEL_ID = os.getenv('DB_CHANNEL_ID')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
TINYURL_API_TOKEN = os.getenv('TINYURL_API_TOKEN')
SUBSCRIPTION_CHANNEL = os.getenv('SUBSCRIPTION_CHANNEL')

if not all([BOT_TOKEN, DB_CHANNEL_ID, ADMIN_IDS]):
    raise ValueError("Missing required environment variables: BOT_TOKEN, DB_CHANNEL_ID, or ADMIN_IDS")

# Initialize bot
bot = Bot(token=BOT_TOKEN)

# In-memory storage
REGISTERED_USERS = set()
FILE_METADATA = {}
BANNED_USERS = set()
USER_SETTINGS = {}  # {chat_id: {notify: bool}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return

    if SUBSCRIPTION_CHANNEL and not await check_subscription(chat_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{SUBSCRIPTION_CHANNEL.lstrip('@')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please join our channel to use this bot!", reply_markup=reply_markup)
        return

    REGISTERED_USERS.add(chat_id)
    USER_SETTINGS[chat_id] = USER_SETTINGS.get(chat_id, {"notify": True})
    keyboard = [
        [InlineKeyboardButton("Upload File", callback_data="upload_file")],
        [InlineKeyboardButton("Help", callback_data="help"), InlineKeyboardButton("Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {user.first_name}!\n"
        "I'm a FileStore bot. Send a file or URL to store it and get shareable links.\n"
        "Use the buttons below to get started!",
        reply_markup=reply_markup
    )

async def check_subscription(chat_id: int) -> bool:
    """Check if user is subscribed to the required channel"""
    try:
        member = await bot.get_chat_member(f"@{SUBSCRIPTION_CHANNEL}", chat_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command or help button"""
    await update.message.reply_text(
        "Commands:\n"
        "- /start: Welcome message\n"
        "- /help: Show this message\n"
        "- /register: Register to use the bot\n"
        "- /stats: View bot usage stats\n"
        "- /search <keyword>: Search stored files\n"
        "- /get_info <message_id>: Get file details\n"
        "- /report <message>: Report an issue\n"
        "- /settings: Manage user settings\n"
        "Admin commands:\n"
        "- /list_files: List all stored files\n"
        "- /delete_file <message_id>: Delete a file\n"
        "- /clear: Clear all files\n"
        "- /ban <user_id>: Ban a user\n"
        "- /unban <user_id>: Unban a user\n"
        "- /broadcast <message>: Send message to all users\n"
        "- /set_expiry <message_id> <hours>: Set file expiry\n"
        "Send a file or URL to store it. Choose link types via buttons."
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if chat_id in REGISTERED_USERS:
        await update.message.reply_text("You're already registered!")
    else:
        REGISTERED_USERS.add(chat_id)
        USER_SETTINGS[chat_id] = {"notify": True}
        await update.message.reply_text("Registration successful! You can now use the bot.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    total_files = len(FILE_METADATA)
    total_size = sum(meta['size'] for meta in FILE_METADATA.values()) / (1024 * 1024)  # MB
    user_count = len(REGISTERED_USERS)
    await update.message.reply_text(
        f"Bot Statistics:\n"
        f"Total Files: {total_files}\n"
        f"Total Size: {total_size:.2f} MB\n"
        f"Registered Users: {user_count}"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search <keyword> command"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /search <keyword>")
        return
    keyword = ' '.join(context.args).lower()
    results = [
        (msg_id, meta) for msg_id, meta in FILE_METADATA.items()
        if keyword in meta['file_name'].lower() or keyword in meta['type'].lower()
    ]
    if not results:
        await update.message.reply_text("No files found matching your search.")
        return
    response = "Search Results:\n"
    for msg_id, meta in results[:10]:  # Limit to 10 results
        response += (
            f"Message ID: {msg_id}\n"
            f"Name: {meta['file_name']}\n"
            f"Type: {meta['type']}\n"
            f"Link: https://t.me/c/{str(DB_CHANNEL_ID).replace('-100', '')}/{msg_id}\n\n"
        )
    await update.message.reply_text(response)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command (admin-only)"""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    try:
        for msg_id in list(FILE_METADATA.keys()):
            await bot.delete_message(chat_id=DB_CHANNEL_ID, message_id=msg_id)
        FILE_METADATA.clear()
        await update.message.reply_text("All stored files have been cleared.")
    except TelegramError as e:
        logger.error(f"Error clearing files: {e}")
        await update.message.reply_text("Error clearing files.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban <user_id> command (admin-only)"""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        user_id = int(context.args[0])
        BANNED_USERS.add(user_id)
        REGISTERED_USERS.discard(user_id)
        await update.message.reply_text(f"User {user_id} has been banned.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban <user_id> command (admin-only)"""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        user_id = int(context.args[0])
        BANNED_USERS.discard(user_id)
        await update.message.reply_text(f"User {user_id} has been unbanned.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast <message> command (admin-only)"""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = ' '.join(context.args)
    success_count = 0
    for user_id in REGISTERED_USERS:
        try:
            if USER_SETTINGS.get(user_id, {}).get("notify", True):
                await bot.send_message(chat_id=user_id, text=f"Broadcast: {message}")
                success_count += 1
        except TelegramError:
            continue
    await update.message.reply_text(f"Broadcast sent to {success_count} users.")

async def set_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_expiry <message_id> <hours> command (admin-only)"""
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set_expiry <message_id> <hours>")
        return
    try:
        message_id = int(context.args[0])
        hours = float(context.args[1])
        if message_id in FILE_METADATA:
            FILE_METADATA[message_id]["expiry"] = datetime.utcnow() + timedelta(hours=hours)
            await update.message.reply_text(
                f"File {message_id} expiry set to {FILE_METADATA[message_id]['expiry'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
        else:
            await update.message.reply_text("File not found.")
    except (ValueError, KeyError):
        await update.message.reply_text("Invalid message ID or hours.")

async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /get_info <message_id> command"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /get_info <message_id>")
        return
    try:
        message_id = int(context.args[0])
        if message_id in FILE_METADATA:
            meta = FILE_METADATA[message_id]
            expiry = meta.get('expiry', 'None')
            if isinstance(expiry, datetime):
                expiry = expiry.strftime('%Y-%m-%d %H:%M:%S UTC')
            await update.message.reply_text(
                f"File Info:\n"
                f"Message ID: {message_id}\n"
                f"Name: {meta['file_name']}\n"
                f"Size: {(meta['size'] / 1024):.2f} KB\n"
                f"Type: {meta['type']}\n"
                f"Uploaded by: {meta['user_id']}\n"
                f"Time: {meta['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"Expiry: {expiry}\n"
                f"Link: https://t.me/c/{str(DB_CHANNEL_ID).replace('-100', '')}/{message_id}"
            )
        else:
            await update.message.reply_text("File not found.")
    except ValueError:
        await update.message.reply_text("Invalid message ID.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report <message> command"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /report <message>")
        return
    message = ' '.join(context.args)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"Report from user {chat_id}:\n{message}"
            )
        except TelegramError:
            continue
    await update.message.reply_text("Your report has been sent to the admins.")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command or settings button"""
    chat_id = update.effective_chat.id
    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    current_settings = USER_SETTINGS.get(chat_id, {"notify": True})
    keyboard = [
        [InlineKeyboardButton(
            f"Notifications: {'On' if current_settings['notify'] else 'Off'}",
            callback_data="toggle_notify"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Your Settings:\nNotifications: {'On' if current_settings['notify'] else 'Off'}",
        reply_markup=reply_markup
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files sent directly to the bot"""
    message = update.message
    chat_id = update.effective_chat.id

    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if SUBSCRIPTION_CHANNEL and not await check_subscription(chat_id):
        await message.reply_text("Please join the required channel to use this bot!")
        return
    if chat_id not in REGISTERED_USERS:
        await message.reply_text("Please register using /register first!")
        return

    files = []
    if message.document:
        files.append((message.document.file_id, message.document.file_name or "document", message.document.mime_type, message.document.file_size))
    elif message.photo:
        files.append((message.photo[-1].file_id, f"photo_{message.message_id}.jpg", "image/jpeg", message.photo[-1].file_size))
    elif message.video:
        files.append((message.video.file_id, message.video.file_name or f"video_{message.message_id}.mp4", message.video.mime_type, message.video.file_size))
    elif message.audio:
        files.append((message.audio.file_id, message.audio.file_name or f"audio_{message.message_id}.mp3", message.audio.mime_type, message.audio.file_size))
    else:
        await message.reply_text("Please send a valid file (photo, video, document, or audio).")
        return

    for file_id, file_name, file_type, file_size in files:
        try:
            sent_message = await bot.send_document(
                chat_id=DB_CHANNEL_ID,
                document=file_id,
                caption=f"Uploaded by user {chat_id}"
            )

            FILE_METADATA[sent_message.message_id] = {
                "file_name": file_name,
                "size": file_size,
                "type": file_type,
                "user_id": chat_id,
                "timestamp": datetime.utcnow()
            }

            keyboard = [
                [InlineKeyboardButton("Telegram Link", callback_data=f"link_telegram_{sent_message.message_id}")],
                [InlineKeyboardButton("Short URL", callback_data=f"link_short_{sent_message.message_id}")],
                [InlineKeyboardButton("Expiring Link (1h)", callback_data=f"link_expire_1h_{sent_message.message_id}")],
                [InlineKeyboardButton("Expiring Link (24h)", callback_data=f"link_expire_24h_{sent_message.message_id}")],
                [InlineKeyboardButton("Expiring Link (7d)", callback_data=f"link_expire_7d_{sent_message.message_id}")]
            ]
            if chat_id in ADMIN_IDS:
                keyboard.append([InlineKeyboardButton("Delete File", callback_data=f"delete_file_{sent_message.message_id}")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await message.reply_text(
                f"File stored successfully!\n"
                f"Name: {file_name}\n"
                f"Size: {(file_size / 1024):.2f} KB\n"
                f"Type: {file_type}\n"
                "Choose a link type:",
                reply_markup=reply_markup
            )
        except TelegramError as e:
            logger.error(f"Error storing file: {e}")
            await message.reply_text("Error storing the file. Please try again.")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URLs sent to the bot"""
    message = update.message
    chat_id = update.effective_chat.id
    url = message.text.strip()

    if chat_id in BANNED_USERS:
        await update.message.reply_text("You are banned from using this bot.")
        return
    if SUBSCRIPTION_CHANNEL and not await check_subscription(chat_id):
        await message.reply_text("Please join the required channel to use this bot!")
        return
    if chat_id not in REGISTERED_USERS:
        await message.reply_text("Please register using /register first!")
        return

    if not re.match(r'^https?://', url):
        await message.reply_text("Please send a valid URL starting with http:// or https://")
        return

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            await message.reply_text("Failed to download the file from the URL.")
            return

        content_disposition = response.headers.get('content-disposition')
        file_name = content_disposition.split('filename=')[1].strip('"') if content_disposition and 'filename=' in content_disposition else os.path.basename(urllib.parse.urlparse(url).path) or "downloaded_file"
        file_size = int(response.headers.get('content-length', 0))
        content_type = response.headers.get('content-type', 'application/octet-stream')

        temp_file_path = f"temp_{file_name}"
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with open(temp_file_path, 'rb') as f:
            sent_message = await bot.send_document(
                chat_id=DB_CHANNEL_ID,
                document=f,
                caption=f"Uploaded by user {chat_id} from URL: {url}"
            )

        FILE_METADATA[sent_message.message_id] = {
            "file_name": file_name,
            "size": file_size,
            "type": content_type,
            "user_id": chat_id,
            "timestamp": datetime.utcnow()
        }

        keyboard = [
            [InlineKeyboardButton("Telegram Link", callback_data=f"link_telegram_{sent_message.message_id}")],
            [InlineKeyboardButton("Short URL", callback_data=f"link_short_{sent_message.message_id}")],
            [InlineKeyboardButton("Expiring Link (1h)", callback_data=f"link_expire_1h_{sent_message.message_id}")],
            [InlineKeyboardButton("Expiring Link (24h)", callback_data=f"link_expire_24h_{sent_message.message_id}")],
            [InlineKeyboardButton("Expiring Link (7d)", callback_data=f"link_expire_7d_{sent_message.message_id}")]
        ]
        if chat_id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("Delete File", callback_data=f"delete_file_{sent_message.message_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(
            f"File stored successfully!\n"
            f"Name: {file_name}\n"
            f"Size: {(file_size / 1024):.2f} KB\n"
            f"Type: {content_type}\n"
            "Choose a link type:",
            reply_markup=reply_markup
        )

        os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        await message.reply_text("Error processing the URL. Please try again.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data == "upload_file":
        await query.message.reply_text("Please send a file or a URL to store.")
        await query.answer()
        return

    if data == "help":
        await query.message.reply_text(
            "Send a file or URL to store it. Choose a link type from the options provided.\n"
            "Admins can use /list_files, /delete_file, /clear, /ban, /unban, /broadcast, /set_expiry."
        )
        await query.answer()
        return

    if data == "settings":
        current_settings = USER_SETTINGS.get(chat_id, {"notify": True})
        keyboard = [
            [InlineKeyboardButton(
                f"Notifications: {'On' if current_settings['notify'] else 'Off'}",
                callback_data="toggle_notify"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            f"Your Settings:\nNotifications: {'On' if current_settings['notify'] else 'Off'}",
            reply_markup=reply_markup
        )
        await query.answer()
        return

    if data == "toggle_notify":
        USER_SETTINGS[chat_id]["notify"] = not USER_SETTINGS.get(chat_id, {"notify": True})["notify"]
        keyboard = [
            [InlineKeyboardButton(
                f"Notifications: {'On' if USER_SETTINGS[chat_id]['notify'] else 'Off'}",
                callback_data="toggle_notify"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            f"Your Settings:\nNotifications: {'On' if USER_SETTINGS[chat_id]['notify'] else 'Off'}",
            reply_markup=reply_markup
        )
        await query.answer()
        return

    if data.startswith("link_"):
        try:
            parts = data.split("_")
            link_type = parts[1]
            message_id = int(parts[2] if link_type != "expire" else parts[3])
            telegram_link = f"https://t.me/c/{str(DB_CHANNEL_ID).replace('-100', '')}/{message_id}"

            if link_type == "telegram":
                await query.message.reply_text(f"Telegram Link: {telegram_link}")
            elif link_type == "short":
                if not TINYURL_API_TOKEN:
                    await query.message.reply_text("Short URL feature is disabled. Contact admin.")
                else:
                    short_url = shorten_url(telegram_link)
                    await query.message.reply_text(f"Short URL: {short_url}")
            elif link_type == "expire":
                duration = parts[2]
                hours = {"1h": 1, "24h": 24, "7d": 168}[duration]
                expiry = datetime.utcnow() + timedelta(hours=hours)
                FILE_METADATA[message_id]["expiry"] = expiry
                await query.message.reply_text(
                    f"Expiring Link (valid until {expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}): {telegram_link}"
                )
            await query.answer()
        except Exception as e:
            logger.error(f"Error generating link: {e}")
            await query.answer("Error generating link.")

    elif data.startswith("delete_file_"):
        if chat_id not in ADMIN_IDS:
            await query.answer("You are not authorized to delete files.")
            return
        try:
            message_id = int(data.split("_")[2])
            await bot.delete_message(chat_id=DB_CHANNEL_ID, message_id=message_id)
            if message_id in FILE_METADATA:
                del FILE_METADATA[message_id]
            await query.message.reply_text(f"File with message ID {message_id} deleted.")
            await query.answer()
        except TelegramError as e:
            logger.error(f"Error deleting file: {e}")
            await query.answer("Error deleting file.")

def shorten_url(url: str) -> str:
    """Shorten URL using TinyURL API"""
    api_url = "https://api.tinyurl.com/create"
    headers = {"Authorization": f"Bearer {TINYURL_API_TOKEN}", "Content-Type": "application/json"}
    data = {"url": url, "domain": "tinyurl.com"}
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["data"]["tiny_url"]
    return url

def main():
    """Run the bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("set_expiry", set_expiry))
    application.add_handler(CommandHandler("get_info", get_info))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("settings", settings))

    # Message handlers
    application.add_handler(MessageHandler(
        filters.Document | filters.Photo | filters.Video | filters.Audio,
        handle_file
    ))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Button handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

 אם __name__ == "__main__":
    main()
