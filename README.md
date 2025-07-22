# QR Library Telegram Bot

A simple Telegram bot to manage a paper book library using QR codes. Built with `python-telegram-bot` 20+.

## Installation

1. Install Python dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

2. Copy `config.py.example` to `config.py` and set your bot token and administrator Telegram IDs.

## Usage

Run the bot with:

```bash
python main.py
```

Users register via `/start` and can take or return books using the menu buttons.
Use the `/menu` command at any time to show the main keyboard again.
All data is stored in `data/users.json` and `data/books.json`.

## Project Structure

- `main.py` – bot startup script.
- `handlers/` – handlers for user and admin actions.
- `data/` – JSON files with users and books.
- `config.py` – configuration with bot token and admin IDs.
- `config.py.example` – template to create your own `config.py`.
- `utils.py` – utility functions for data access and checks.



