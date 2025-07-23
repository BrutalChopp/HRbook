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

import importlib
import config
import utils
from handlers import start as start_module
from handlers import books as books_module
from handlers import admin as admin_module


import pytest_asyncio


@pytest_asyncio.fixture
async def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "sqlite")
    monkeypatch.setenv("DB_NAME", str(tmp_path / "test.db"))

    import importlib
    import db
    import utils
    import handlers.start as start_module
    import handlers.books as books_module
    import handlers.admin as admin_module

    importlib.reload(db)
    importlib.reload(utils)
    importlib.reload(start_module)
    importlib.reload(books_module)
    importlib.reload(admin_module)

    await db.init_db()

    # minimal config
    monkeypatch.setattr(config, "BOT_TOKEN", "TEST")
    monkeypatch.setattr(config, "ADMIN_IDS", ["1"])
    monkeypatch.setattr(
        config,
        "OFFICES",
        {"Main": {"admins": ["1"]}, "Alt": {"admins": []}},
    )

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
    application.add_handler(start_module.get_handler())
    application.add_handler(start_module.get_menu_handler())
    application.add_handler(start_module.get_change_office_handler())
    for h in books_module.get_handlers():
        application.add_handler(h)
    for h in admin_module.get_handlers():
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


def make_photo_update(app, user_id=1):
    """Return an Update with a dummy photo message."""
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    photo = telegram.PhotoSize(file_id="file-id", file_unique_id="file-uid", width=1, height=1)
    photo._bot = app.bot
    msg = Message(
        message_id=next(_id_gen),
        date=datetime.now(),
        chat=chat,
        from_user=user,
        photo=[photo],
    )
    msg._bot = app.bot
    return telegram.Update(update_id=next(_id_gen), message=msg)
