import random
import time
from threading import Thread, Event
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

TOKEN = '7462406196:AAH5dPcl6qxFRGwMN7S6x8_NGE2rG4O651Y'
OWNER_USER_ID = '1449777621'

ADD_RED_IMAGE, ADD_GREEN_IMAGE, ADD_STICKER = range(3)

user_running_status = {}
user_channels = {}
user_starting_number = {}
user_stickers = {}
user_red_images = {}
user_green_images = {}
authorized_users = set()
user_threads = {}
user_events = {}

def restricted(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id != OWNER_USER_ID and user_id not in authorized_users:
            update.message.reply_text("You are not authorized to use this bot.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def owner_only(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id != OWNER_USER_ID:
            update.message.reply_text("Only the bot owner can use this command.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def channel_owner_only(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in user_channels:
            update.message.reply_text("You don't have any channels added.")
            return
        return func(update, context, *args, *kwargs)
    return wrapper

@channel_owner_only
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_running_status:
        user_running_status[user_id] = False

    if not user_running_status[user_id]:
        user_running_status[user_id] = True
        update.message.reply_text('Bot started! Messages will be sent every minute.')

        user_events[user_id] = Event()
        user_threads[user_id] = Thread(target=send_messages, args=(context, user_id, user_events[user_id]))
        user_threads[user_id].start()
    else:
        update.message.reply_text('Bot is already running.')

@channel_owner_only
def stop(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_running_status and user_running_status[user_id]:
        user_running_status[user_id] = False
        user_events[user_id].set()
        user_threads[user_id].join()
        update.message.reply_text('Bot stopped!')
    else:
        update.message.reply_text('Bot is already stopped.')

@restricted
def help_command(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id == OWNER_USER_ID:
        update.message.reply_text(
            'Commands:\n'
            '/start - Start the bot\n'
            '/stop - Stop the bot\n'
            '/status - Check bot status\n'
            '/setnumber <number> - Set the starting number for messages\n'
            '/addchannel <channel_id> - Add a channel to send messages\n'
            '/removechannel <channel_id> - Remove a channel from the list\n'
            '/listchannels - List all added channels\n'
            '/addsticker - Add a sticker to the list\n'
            '/done - Finish adding stickers/images\n'
            '/showstickers - Show all added stickers\n'
            '/adduser <user_id> - Add an authorized user (owner only)\n'
            '/removeuser <user_id> - Remove an authorized user (owner only)\n'
            '/listusers - List all authorized users (owner only)\n'
            '/addredimage - Add a red image to the list\n'
            '/showredimages - Show all red images\n'
            '/addgreenimage - Add a green image to the list\n'
            '/showgreenimages - Show all green images\n'
        )
    else:
        update.message.reply_text(
            'Commands:\n'
            '/start - Start the bot\n'
            '/stop - Stop the bot\n'
            '/status - Check bot status\n'
            '/setnumber <number> - Set the starting number for messages\n'
            '/addchannel <channel_id> - Add a channel to send messages\n'
            '/removechannel <channel_id> - Remove a channel from the list\n'
            '/listchannels - List all added channels\n'
            '/addsticker - Add a sticker to the list\n'
            '/done - Finish adding stickers/images\n'
            '/showstickers - Show all added stickers\n'
            '/addredimage - Add a red image to the list\n'
            '/showredimages - Show all red images\n'
            '/addgreenimage - Add a green image to the list\n'
            '/showgreenimages - Show all green images\n'
        )

@restricted
def status(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_running_status and user_running_status[user_id]:
        update.message.reply_text('Bot is running.')
    else:
        update.message.reply_text('Bot is stopped.')

@restricted
def set_number(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    try:
        number = int(context.args[0])
        user_starting_number[user_id] = number
        update.message.reply_text(f'Starting number set to {number}.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /setnumber <number>')

@restricted
def add_channel(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_channels:
        user_channels[user_id] = []

    try:
        channel_id = context.args[0]
        if channel_id not in user_channels[user_id]:
            user_channels[user_id].append(channel_id)
            update.message.reply_text(f'Channel {channel_id} added.')
        else:
            update.message.reply_text(f'Channel {channel_id} is already in the list.')
    except IndexError:
        update.message.reply_text('Usage: /addchannel <channel_id>')

@restricted
def remove_channel(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_channels:
        update.message.reply_text('No channels found for this user.')
        return

    try:
        channel_id = context.args[0]
        if channel_id in user_channels[user_id]:
            user_channels[user_id].remove(channel_id)
            update.message.reply_text(f'Channel {channel_id} removed.')
        else:
            update.message.reply_text(f'Channel {channel_id} not found in the list.')
    except IndexError:
        update.message.reply_text('Usage: /removechannel <channel_id>')

@restricted
def list_channels(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_channels and user_channels[user_id]:
        update.message.reply_text('Added channels:\n' + '\n'.join(user_channels[user_id]))
    else:
        update.message.reply_text('No channels added.')

@owner_only
def add_user(update: Update, context: CallbackContext):
    try:
        user_id = context.args[0]
        authorized_users.add(user_id)
        update.message.reply_text(f'User {user_id} authorized.')
    except IndexError:
        update.message.reply_text('Usage: /adduser <user_id>')

@owner_only
def remove_user(update: Update, context: CallbackContext):
    try:
        user_id = context.args[0]
        if user_id in authorized_users:
            authorized_users.remove(user_id)
            update.message.reply_text(f'User {user_id} unauthorized.')
        else:
            update.message.reply_text(f'User {user_id} not found in authorized list.')
    except IndexError:
        update.message.reply_text('Usage: /removeuser <user_id>')

@owner_only
def list_users(update: Update, context: CallbackContext):
    if authorized_users:
        update.message.reply_text('Authorized users:\n' + '\n'.join(authorized_users))
    else:
        update.message.reply_text('No authorized users.')

@restricted
def add_sticker_start(update: Update, context: CallbackContext):
    update.message.reply_text('Please send the stickers you want to add. Send /done when finished.')
    return ADD_STICKER

def add_sticker_finish(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_stickers:
        user_stickers[user_id] = []

    if update.message.sticker:
        sticker_id = update.message.sticker.file_id
        if sticker_id not in user_stickers[user_id]:
            user_stickers[user_id].append(sticker_id)
            update.message.reply_text('Sticker added. Send more or use /done to finish.')
        else:
            update.message.reply_text('Sticker already in the list. Send more or use /done to finish.')
    else:
        update.message.reply_text('Please send a sticker to add.')
    return ADD_STICKER

@restricted
def add_red_image_start(update: Update, context: CallbackContext):
    update.message.reply_text('Please send the red images you want to add. Send /done when finished.')
    return ADD_RED_IMAGE

def add_red_image_finish(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_red_images:
        user_red_images[user_id] = []

    if update.message.photo:
        image_id = update.message.photo[-1].file_id
        if image_id not in user_red_images[user_id]:
            user_red_images[user_id].append(image_id)
            update.message.reply_text('Red image added. Send more or use /done to finish.')
        else:
            update.message.reply_text('Red image already in the list. Send more or use /done to finish.')
    else:
        update.message.reply_text('Please send an image to add.')
    return ADD_RED_IMAGE

@restricted
def add_green_image_start(update: Update, context: CallbackContext):
    update.message.reply_text('Please send the green images you want to add. Send /done when finished.')
    return ADD_GREEN_IMAGE

def add_green_image_finish(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in user_green_images:
        user_green_images[user_id] = []

    if update.message.photo:
        image_id = update.message.photo[-1].file_id
        if image_id not in user_green_images[user_id]:
            user_green_images[user_id].append(image_id)
            update.message.reply_text('Green image added. Send more or use /done to finish.')
        else:
            update.message.reply_text('Green image already in the list. Send more or use /done to finish.')
    else:
        update.message.reply_text('Please send an image to add.')
    return ADD_GREEN_IMAGE

@restricted
def done(update: Update, context: CallbackContext):
    update.message.reply_text('Finished adding stickers/images.')
    return ConversationHandler.END

@restricted
def show_stickers(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_stickers and user_stickers[user_id]:
        stickers = user_stickers[user_id]
        update.message.reply_text('Your stickers:')
        for sticker_id in stickers:
            context.bot.send_sticker(chat_id=user_id, sticker=sticker_id)
    else:
        update.message.reply_text('No stickers added.')

@restricted
def show_red_images(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_red_images and user_red_images[user_id]:
        images = user_red_images[user_id]
        update.message.reply_text('Your red images:')
        for image_id in images:
            context.bot.send_photo(chat_id=user_id, photo=image_id)
    else:
        update.message.reply_text('No red images added.')

@restricted
def show_green_images(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in user_green_images and user_green_images[user_id]:
        images = user_green_images[user_id]
        update.message.reply_text('Your green images:')
        for image_id in images:
            context.bot.send_photo(chat_id=user_id, photo=image_id)
    else:
        update.message.reply_text('No green images added.')

def send_messages(context, user_id, event):
    if user_id not in user_starting_number:
        context.bot.send_message(chat_id=user_id, text="Please set a starting number using /setnumber <number> before starting the bot.")
        user_running_status[user_id] = False
        return

    number = user_starting_number[user_id]
    choices = ["...........Big", "..........Small"]
    colors = ["Red", "Green"]

    channels = user_channels.get(user_id, [])
    stickers = user_stickers.get(user_id, [])
    red_images = user_red_images.get(user_id, [])
    green_images = user_green_images.get(user_id, [])

    sticker_index = 0
    red_image_index = 0
    green_image_index = 0

    while user_running_status.get(user_id, False):
        if event.is_set():
            break
        selected_text = random.choice(choices)
        selected_color = random.choice(colors)
        message = f"{number} {selected_text} {selected_color}"
        print(f"Sending message: {message}")

        for channel in channels:
            try:
                context.bot.send_message(chat_id=channel, text=message)
                print(f"Message sent to channel: {channel}")

                if stickers:
                    try:
                        context.bot.send_sticker(chat_id=channel, sticker=stickers[sticker_index])
                        print(f"Sticker sent to channel: {channel}")
                    except Exception as e:
                        print(f"Failed to send sticker to {channel}: {e}")

                    sticker_index = (sticker_index + 1) % len(stickers)

                if "Red" in selected_color and red_images:
                    try:
                        context.bot.send_photo(chat_id=channel, photo=red_images[red_image_index])
                        print(f"Red image sent to channel: {channel}")
                    except Exception as e:
                        print(f"Failed to send red image to {channel}: {e}")

                    red_image_index = (red_image_index + 1) % len(red_images)

                if "Green" in selected_color and green_images:
                    try:
                        context.bot.send_photo(chat_id=channel, photo=green_images[green_image_index])
                        print(f"Green image sent to channel: {channel}")
                    except Exception as e:
                        print(f"Failed to send green image to {channel}: {e}")

                    green_image_index = (green_image_index + 1) % len(green_images)

            except Exception as e:
                print(f"Failed to send message to {channel}: {e}")

        number += 1
        user_starting_number[user_id] = number
        event.wait(60)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("setnumber", set_number))
    dp.add_handler(CommandHandler("addchannel", add_channel))
    dp.add_handler(CommandHandler("removechannel", remove_channel))
    dp.add_handler(CommandHandler("listchannels", list_channels))
    dp.add_handler(CommandHandler("adduser", add_user))
    dp.add_handler(CommandHandler("removeuser", remove_user))
    dp.add_handler(CommandHandler("listusers", list_users))

    add_sticker_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addsticker', add_sticker_start)],
        states={
            ADD_STICKER: [MessageHandler(Filters.sticker & Filters.private, add_sticker_finish)]
        },
        fallbacks=[CommandHandler('done', done)]
    )

    add_red_image_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addredimage', add_red_image_start)],
        states={
            ADD_RED_IMAGE: [MessageHandler(Filters.photo, add_red_image_finish)]
        },
        fallbacks=[CommandHandler('done', done)]
    )

    add_green_image_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addgreenimage', add_green_image_start)],
        states={
            ADD_GREEN_IMAGE: [MessageHandler(Filters.photo, add_green_image_finish)]
        },
        fallbacks=[CommandHandler('done', done)]
    )

    dp.add_handler(add_sticker_conv_handler)
    dp.add_handler(add_red_image_conv_handler)
    dp.add_handler(add_green_image_conv_handler)

    dp.add_handler(CommandHandler("showstickers", show_stickers))
    dp.add_handler(CommandHandler("showredimages", show_red_images))
    dp.add_handler(CommandHandler("showgreenimages", show_green_images))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()



