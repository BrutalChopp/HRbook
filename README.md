# QR Library Telegram Bot

A simple Telegram bot to manage a paper book library using QR codes. Built with `python-telegram-bot` 20+.
Documentation in Russian is available in the [docs](docs/README_RU.md) folder.

## Installation

1. Install Python dependencies from `requirements.txt` (this includes Pillow):

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set your bot token and administrator Telegram IDs.

## Network Access

This bot requires outgoing HTTPS access to `api.telegram.org`. If the domain is blocked you will see `NetworkError: httpx.ProxyError`.

### Troubleshooting

- Ensure the host or container has internet access.
- Check that you can reach `https://api.telegram.org` using `curl` or similar.
- Configure your proxy or firewall to allow outbound requests to this domain.

## Usage

Set the `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT` variables to connect to your PostgreSQL instance. Run the bot with:

```bash
python main.py
```

Users register via `/start` and can take or return books using the menu buttons.
When starting the bot you will see a short welcome message describing its purpose.
During any step you can press the "↩️ Назад" button to cancel the current action
and return to the main menu. Use the `/menu` command at any time to show the main keyboard again.
Use the "📖 Все книги" button to see a list of all books with their current status.
Administrators receive additional menu options for managing the library: adding books, generating reports, resetting book status and viewing the list of users.
All data is stored in a database configured via environment variables. By default the bot expects a PostgreSQL server, but you can set `DB_ENGINE=sqlite` to run with a local SQLite file (used in the tests).

## Project Structure

- `main.py` – bot startup script.
- `handlers/` – handlers for user and admin actions.
- Database tables are created automatically in the configured engine.
- `config.py` – loads configuration from environment variables.
- `.env.example` – template to create your own `.env`.
- `utils.py` – utility functions for data access and checks.

## Docker

Build the image locally:

```bash
docker build -t hrbook:latest .
```

Tag the resulting image and push it to Yandex Container Registry:

```bash
docker tag hrbook:latest cr.yandex/<registry>/<image>:<tag>
docker push cr.yandex/<registry>/<image>:<tag>
```

Reference the pushed tag in your deployment configuration so that the correct
image version is used.

## Testing

Run the unit tests with:

```bash
pytest
```

## Avoiding 409 Conflict Errors

Telegram returns `409 Conflict` if more than one instance of the bot polls for
updates using the same token. The startup script now creates a lock file at
`/tmp/hrbook_bot.lock` to ensure only a single bot process runs. If you see an
error similar to `terminated by other getUpdates request`, make sure no other
process is running and remove the lock file if necessary.


