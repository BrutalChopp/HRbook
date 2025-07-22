# QR Library Telegram Bot

A simple Telegram bot to manage a paper book library using QR codes. Built with `python-telegram-bot` 20+.

## Installation

1. Install Python dependencies:

```bash
pip install python-telegram-bot==20.*
```

2. Copy `config_template.py` to `config.py` (or create it yourself) and
   provide the required environment variables.

## Usage

Run the bot with:

```bash
python main.py
```

Users register via `/start` and can take or return books using the menu buttons.
Use the `/menu` command at any time to show the main keyboard again.
All data is stored in `data/users.json` and `data/books.json`.

### Environment Variables

Set the following variables in your shell or `.env` file:

- `BOT_TOKEN` – Telegram bot token obtained from BotFather.
- `ADMIN_IDS` – comma-separated list of Telegram user IDs that have admin access.

## Project Structure

- `main.py` – bot startup script.
- `handlers/` – handlers for user and admin actions.
- `data/` – JSON files with users and books.
- `config.py` – configuration that reads the token and admin IDs from environment variables.
- `utils.py` – utility functions for data access and checks.



