import json
from datetime import datetime
import itertools
import types
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
import telegram
from telegram import User, Chat, Message, MessageEntity
from telegram.ext import Application

import config
import utils
from handlers.start import get_handler as start_handler, get_menu_handler
from handlers.books import get_handlers as books_handlers
from handlers.admin import get_handlers as admin_handlers


import pytest_asyncio


@pytest_asyncio.fixture
async def app(tmp_path, monkeypatch):
    # configure temporary data directory
    monkeypatch.setattr(utils, "DATA_DIR", tmp_path)
    (tmp_path / "users.json").write_text("[]", encoding="utf-8")
    (tmp_path / "books.json").write_text("[]", encoding="utf-8")

    # minimal config
    monkeypatch.setattr(config, "BOT_TOKEN", "TEST")
    monkeypatch.setattr(config, "ADMIN_IDS", ["1"])
    monkeypatch.setattr(config, "OFFICES", {"Main": {"admins": ["1"]}})

    sent_messages = []

    async def fake_do_post(self, endpoint, data, *args, **kwargs):
        if endpoint == "sendMessage":
            sent_messages.append(data["text"])
            return {
                "message_id": len(sent_messages),
                "date": 0,
                "chat": {"id": data["chat_id"], "type": "private"},
                "text": data["text"],
            }
        return {"ok": True, "result": True}

    async def dummy_initialize(self):
        self._initialized = True
        self._bot_user = User(
            id=999, is_bot=True, first_name="TestBot", username="testbot"
        )

    monkeypatch.setattr(telegram.Bot, "_do_post", fake_do_post)
    monkeypatch.setattr(telegram.Bot, "initialize", dummy_initialize)

    application = Application.builder().token("TEST").build()
    application.add_handler(start_handler())
    application.add_handler(get_menu_handler())
    for h in books_handlers():
        application.add_handler(h)
    for h in admin_handlers():
        application.add_handler(h)

    await application.initialize()
    yield application, sent_messages, tmp_path
    await application.shutdown()


_id_gen = itertools.count(1)


def make_update(app, text, user_id=1):
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    entities = None
    if text.startswith("/"):
        entities = [MessageEntity(type="bot_command", offset=0, length=len(text))]
    msg = Message(
        message_id=next(_id_gen),
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
        entities=entities,
    )
    msg._bot = app.bot
    return telegram.Update(update_id=next(_id_gen), message=msg)
