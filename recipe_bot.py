import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_CHANNEL_ID = os.getenv('DB_CHANNEL_ID')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

if not all([BOT_TOKEN, DB_CHANNEL_ID, ADMIN_IDS]):
    raise ValueError("Missing required environment variables")

bot = Bot(token=BOT_TOKEN)

RECIPES = {}  # {recipe_id: {name, ingredients, instructions, user_id}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Add Recipe", callback_data="add_recipe")],
        [InlineKeyboardButton("Search Recipe", callback_data="search_recipe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Recipe Sharing Bot!\nShare and discover delicious recipes.",
        reply_markup=reply_markup
    )

async def add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter: /add_recipe <name> <ingredients> <instructions>")

async def handle_add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /add_recipe <name> <ingredients> <instructions>")
        return
    name = args[0]
    ingredients = args[1]
    instructions = ' '.join(args[2:])
    recipe_id = len(RECIPES) + 1
    RECIPES[recipe_id] = {"name": name, "ingredients": ingredients, "instructions": instructions, "user_id": chat_id}
    await bot.send_message(
        chat_id=DB_CHANNEL_ID,
        text=f"Recipe: {name}\nIngredients: {ingredients}\nInstructions: {instructions}\nBy user {chat_id}"
    )
    await update.message.reply_text(f"Added recipe: {name}")

async def search_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /search_recipe <keyword>")
        return
    keyword = ' '.join(args).lower()
    results = [r for r in RECIPES.values() if keyword in r['name'].lower()]
    if not results:
        await update.message.reply_text("No recipes found.")
        return
    response = "Recipes:\n"
    for recipe in results[:5]:
        response += f"Name: {recipe['name']}\nIngredients: {recipe['ingredients']}\nInstructions: {recipe['instructions']}\n\n"
    await update.message.reply_text(response)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("Please send a valid URL.")
        return
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1') or 'Recipe'
        name = name.text.strip() if name else 'Untitled Recipe'
        ingredients = [li.text.strip() for li in soup.find_all('li') if 'ingredient' in li.text.lower()][:5]
        instructions = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 50][:3]
        recipe_id = len(RECIPES) + 1
        RECIPES[recipe_id] = {
            "name": name,
            "ingredients": '; '.join(ingredients) or "Unknown",
            "instructions": ' '.join(instructions) or "Unknown",
            "user_id": chat_id
        }
        await bot.send_message(
            chat_id=DB_CHANNEL_ID,
            text=f"Recipe from URL: {name}\nBy user {chat_id}"
        )
        await update.message.reply_text(f"Added recipe from URL: {name}")
    except Exception as e:
        logger.error(f"Error scraping URL: {e}")
        await update.message.reply_text("Error scraping recipe from URL.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "add_recipe":
        await query.message.reply_text("Enter: /add_recipe <name> <ingredients> <instructions>")
    elif data == "search_recipe":
        await query.message.reply_text("Enter: /search_recipe <keyword>")
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_recipe", handle_add_recipe))
    application.add_handler(CommandHandler("search_recipe", search_recipe))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()