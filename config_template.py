"""Example configuration loaded from environment variables."""

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Comma-separated list of Telegram user IDs with admin rights
ADMIN_IDS = [int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",") if uid]
