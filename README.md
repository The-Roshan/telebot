# FileStore Telegram Bot

## Overview
This is an advanced Telegram bot built with Python for storing files or URLs and generating shareable links. It offers multiple link types, user management, and extensive admin controls. Files are stored in a private Telegram channel, accessible via generated links.

## Features
- **File Storage**: Store documents, photos, videos, or audio in a private channel.
- **URL Support**: Download and store files from URLs.
- **Link Options**: Telegram link, Short URL (TinyURL), Expiring links (1h, 24h, 7d).
- **File Metadata**: Display name, size, type, and upload time.
- **Multiple File Support**: Handle multiple files in one message.
- **User Registration**: Restrict access via `/register`.
- **Force Subscription**: Optional channel subscription requirement.
- **Admin Controls**:
  - List, delete, or clear files.
  - Ban/unban users.
  - Broadcast messages.
  - Set custom file expiry.
- **User Features**:
  - Search files by name or type.
  - Report issues to admins.
  - Toggle notification settings.
- **Inline Keyboards**: Buttons for link selection, settings, and admin actions.
- **Commands**:
  - `/start`: Welcome message with buttons.
  - `/help`: Usage instructions.
  - `/register`: Register to use the bot.
  - `/stats`: View bot usage stats.
  - `/search <keyword>`: Search stored files.
  - `/get_info <message_id>`: Get file details.
  - `/report <message>`: Report an issue.
  - `/settings`: Manage user settings.
  - `/list_files`: List all files (admin-only).
  - `/delete_file <message_id>`: Delete a file (admin-only).
  - `/clear`: Clear all files (admin-only).
  - `/ban <user_id>`: Ban a user (admin-only).
  - `/unban <user_id>`: Unban a user (admin-only).
  - `/broadcast <message>`: Send message to all users (admin-only).
  - `/set_expiry <message_id> <hours>`: Set file expiry (admin-only).

## Tech Stack
- **Language**: Python 3.10+
- **Library**: python-telegram-bot (v21.6)
- **Dependencies**: requests, python-dotenv
- **Services**: TinyURL API (optional)
- **Storage**: Telegram private channel
- **Deployment**: Local, VPS, Heroku, or Docker

## Prerequisites
- **Python**: 3.10 or higher
- **Telegram Account**: For bot and channel creation
- **Bot Token**: From [@BotFather](https://t.me/BotFather)
- **Channel ID**: Private Telegram channel for storage
- **Admin IDs**: Telegram user IDs for admins
- **TinyURL API Token** (optional): For shortened URLs
- **Subscription Channel** (optional): For force-sub

## Setup Instructions

### 1. Create a Telegram Bot
1. Chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, follow prompts, and copy the **BOT_TOKEN**.

### 2. Create a Private Channel
1. Create a private Telegram channel.
2. Add your bot as an admin with posting permissions.
3. Get the channel ID using [@MissRose_bot](https://t.me/MissRose_bot) with `/id`.

### 3. Get Admin IDs
1. Send `/id` to [@MissRose_bot](https://t.me/MissRose_bot) in a private chat.
2. Note IDs for all admins (comma-separated in `.env`).

### 4. Get TinyURL API Token (Optional)
1. Sign up at [TinyURL](https://tinyurl.com/app/dev).
2. Generate an API token.

### 5. Clone the Repository
```bash
git clone https://The-Roshan/telebot.git
cd filestore-bot
```

### 6. Install Dependencies
```bash
pip install -r requirements.txt
```

### 7. Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env`:
   ```
   BOT_TOKEN=your_bot_token_here
   DB_CHANNEL_ID=-1001234567890
   ADMIN_IDS=123456789,987654321
   TINYURL_API_TOKEN=your_tinyurl_api_token
   SUBSCRIPTION_CHANNEL=@YourChannel
   ```

### 8. Run the Bot
```bash
python bot.py
```

## Usage
1. Start a chat with your bot.
2. Send `/start` to see the welcome message and buttons.
3. Register with `/register` if required.
4. Join the subscription channel if enabled.
5. Send a file or URL to store it.
6. Select a link type via inline buttons.
7. Use `/stats`, `/search`, `/get_info`, or `/report` for additional actions.
8. Admins can use `/list_files`, `/delete_file`, `/clear`, `/ban`, `/unban`, `/broadcast`, or `/set_expiry`.

## Project Structure
```
filestore-bot/
├── bot.py                  # Main bot script
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
├── LICENSE.md             # MIT License
└── README.md             # This file
```

## Deployment
- **Local/VPS**:
  ```bash
  tmux
  python bot.py
  ```
- **Heroku**:
  1. Create a Heroku app.
  2. Set environment variables.
  3. Push to Heroku:
     ```bash
     heroku git:push heroku main
     ```
- **Docker**:
  ```dockerfile
  FROM python:3.10-slim
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  CMD ["python", "bot.py"]
  ```
  ```bash
  docker build -t filestore-bot .
  docker run --env-file .env -d filestore-bot
  ```

## Notes
- **File Size Limit**: 20MB (extend to 2GB with a local Bot API server).
- **Expiring Links**: Managed in-memory; use a database for persistence.
- **Security**: Keep the storage channel private.
- **Customization**: Add auto-delete or custom captions as needed.

## License
This project is licensed under the MIT License. See `LICENSE.md` for details.

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## Acknowledgments
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [TinyURL API](https://tinyurl.com/app/dev)
- Inspired by [CodeXBotz/File-Sharing-Bot](https://github.com/CodeXBotz/File-Sharing-Bot)

## Contact
Open an issue on GitHub for questions or feedback.







# Telegram Bots Collection

## Overview
This repository contains five Telegram bots built with Python for various use cases: Personal Finance Tracker, Event Scheduler, Learning Flashcard, Recipe Sharing, and Task Manager. Each bot stores data in a private Telegram channel and uses inline buttons for interaction.

## Bots

### 1. Personal Finance Tracker Bot
- **Purpose**: Track expenses and income, categorize transactions, and generate reports.
- **Features**:
  - Commands: `/start`, `/add_expense <amount> <category>`, `/add_income <amount> <source>`, `/stats`.
  - Upload receipt images for automatic expense extraction (OCR).
  - Inline buttons for adding transactions or viewing stats.
- **Storage**: Transactions logged in a private channel.

### 2. Event Scheduler Bot
- **Purpose**: Organize events, create polls, and send reminders.
- **Features**:
  - Commands: `/start`, `/create_event <name> <date>`, `/list_events`.
  - Inline buttons for RSVPs and event creation.
- **Storage**: Event details stored in a private channel.

### 3. Learning Flashcard Bot
- **Purpose**: Study with digital flashcards, create decks, and take quizzes.
- **Features**:
  - Commands: `/start`, `/add_card <deck_name> <question> <answer>`, `/quiz <deck_name>`.
  - Inline buttons for adding cards or showing quiz answers.
- **Storage**: Flashcards stored in a private channel.

### 4. Recipe Sharing Bot
- **Purpose**: Share, search, and save recipes, with web scraping support.
- **Features**:
  - Commands: `/start`, `/add_recipe <name> <ingredients> <instructions>`, `/search_recipe <keyword>`.
  - Send URLs to scrape recipes from websites.
  - Inline buttons for adding or searching recipes.
- **Storage**: Recipes stored in a private channel.

### 5. Task Manager Bot
- **Purpose**: Manage tasks with deadlines and assignments, with reminders.
- **Features**:
  - Commands: `/start`, `/add_task <description> <due_date>`, `/list_tasks`, `/done <task_id>`.
  - Inline buttons for adding or listing tasks.
  - Redis-backed reminders (requires Redis server).
- **Storage**: Tasks stored in a private channel.

## Prerequisites
- **Python**: 3.10 or higher
- **Telegram Account**: For bot and channel creation
- **Bot Token**: From [@BotFather](https://t.me/BotFather)
- **Channel ID**: Private Telegram channel for storage
- **Admin IDs**: Telegram user IDs for admins
- **Subscription Channel** (optional): For force-sub
- **Additional**:
  - Tesseract OCR for Finance Bot (install separately).
  - Redis server for Task Bot reminders (install locally or use a hosted service).

## Setup Instructions

### 1. Create a Telegram Bot
1. Chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, follow prompts, and copy the **BOT_TOKEN**.

### 2. Create a Private Channel
1. Create a private Telegram channel.
2. Add your bot as an admin with posting permissions.
3. Get the channel ID using [@MissRose_bot](https://t.me/MissRose_bot) with `/id`.

### 3. Get Admin IDs
1. Send `/id` to [@MissRose_bot](https://t.me/MissRose_bot) in a private chat.
2. Note IDs for admins (comma-separated in `.env`).

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
- Install Tesseract OCR for Finance Bot (see [pytesseract docs](https://pypi.org/project/pytesseract/)).
- Install and run Redis for Task Bot (`sudo apt-get install redis-server` on Ubuntu).

### 5. Configure Environment Variables
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env`:
   ```
   BOT_TOKEN=your_bot_token_here
   DB_CHANNEL_ID=-1001234567890
   ADMIN_IDS=123456789,987654321
   SUBSCRIPTION_CHANNEL=@YourChannel
   ```

### 6. Run a Bot
Navigate to the bot’s directory and run:
```bash
python bot.py
```
Replace `bot.py` with the specific bot file (e.g., `finance_bot.py`).

## Project Structure
```
telegram-bots/
├── finance_bot.py          # Personal Finance Tracker Bot
├── event_bot.py           # Event Scheduler Bot
├── flashcard_bot.py       # Learning Flashcard Bot
├── recipe_bot.py          # Recipe Sharing Bot
├── task_bot.py            # Task Manager Bot
├── requirements.txt       # Shared dependencies
├── .env.example           # Environment variables template
├── LICENSE.md             # MIT License
└── README.md             # This file
```

## Deployment
- **Local/VPS**:
  ```bash
  tmux
  python bot.py
  ```
- **Heroku**:
  1. Create a Heroku app.
  2. Set environment variables.
  3. Push to Heroku:
     ```bash
     heroku git:push heroku main
     ```
- **Docker**:
  ```dockerfile
  FROM python:3.10-slim
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  CMD ["python", "bot.py"]
  ```
  ```bash
  docker build -t telegram-bot .
  docker run --env-file .env -d telegram-bot
  ```
  Replace `bot.py` with the desired bot file.

## Notes
- **File Size Limit**: 20MB for Telegram uploads (extend with local Bot API server).
- **Data Persistence**: In-memory storage; use a database for production.
- **Security**: Keep storage channels private.
- **Customization**: Add features like subscription checks or admin commands.

## License
This project is licensed under the MIT License. See `LICENSE.md` for details.

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## Acknowledgments
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- Inspired by community-driven Telegram bot projects

## Contact
Open an issue on GitHub for questions or feedback.
