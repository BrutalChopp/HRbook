import pytest

from handlers.start import LAST_NAME, FIRST_NAME, OFFICE
import utils
import sqlite3
from conftest import make_update
from conftest import make_photo_update


@pytest.mark.asyncio
async def test_registration_flow(app):
    application, sent, tmp = app
    # start command
    await application.process_update(make_update(application, "/start", user_id=1))
    assert sent[-1] == "Введите вашу фамилию:"
    # last name
    await application.process_update(make_update(application, "Ivanov"))
    assert sent[-1] == "Введите ваше имя:"
    # first name
    await application.process_update(make_update(application, "Ivan"))
    assert sent[-1] == "Выберите офис:"
    await application.process_update(make_update(application, "Main"))
    assert sent[-1] == "✅ Регистрация успешна."
    conn = sqlite3.connect(tmp / "test.db")
    row = conn.execute(
        "SELECT first_name, office FROM users WHERE telegram_id = 1"
    ).fetchone()
    conn.close()
    assert row[0] == "Ivan"
    assert row[1] == "Main"


@pytest.mark.asyncio
async def test_registration_office_case_insensitive(app):
    application, sent, tmp = app
    await application.process_update(make_update(application, "/start"))
    await application.process_update(make_update(application, "Last"))
    await application.process_update(make_update(application, "First"))
    assert sent[-1] == "Выберите офис:"
    await application.process_update(make_update(application, "main"))
    assert sent[-1] == "✅ Регистрация успешна."
    conn = sqlite3.connect(tmp / "test.db")
    row = conn.execute("SELECT office FROM users").fetchone()
    conn.close()
    assert row[0] == "Main"


@pytest.mark.asyncio
async def test_take_and_return_book(app):
    application, sent, tmp = app
    # register user
    await application.process_update(make_update(application, "/start"))
    await application.process_update(make_update(application, "Last"))
    await application.process_update(make_update(application, "First"))
    await application.process_update(make_update(application, "Main"))
    # prepare book
    utils.save_book(
        {
            "qr_code": "qr1",
            "title": "Book",
            "status": "available",
            "taken_by": None,
            "taken_date": None,
            "office": "Main",
        }
    )
    # take book
    await application.process_update(make_update(application, "🔍 Взять книгу"))
    assert sent[-1] == "Отправьте QR-код книги:"
    await application.process_update(make_update(application, "qr1"))
    assert any("успешно" in m for m in sent[-2:])
    conn = sqlite3.connect(tmp / "test.db")
    status = conn.execute("SELECT status FROM books WHERE qr_code='qr1'").fetchone()[0]
    assert status == "taken"
    # return book
    await application.process_update(make_update(application, "📤 Вернуть книгу"))
    assert sent[-1] == "Отправьте QR-код книги для возврата:"
    await application.process_update(make_update(application, "qr1"))
    status = conn.execute("SELECT status FROM books WHERE qr_code='qr1'").fetchone()[0]
    conn.close()
    assert status == "available"


@pytest.mark.asyncio
async def test_admin_operations(app):
    application, sent, tmp = app
    # admin registration
    await application.process_update(make_update(application, "/start", user_id=1))
    await application.process_update(make_update(application, "Admin"))
    await application.process_update(make_update(application, "User"))
    await application.process_update(make_update(application, "Main"))
    # add book as admin
    await application.process_update(make_update(application, "➕ Добавить книгу"))
    assert sent[-1] == "Отправьте QR-код новой книги:"
    await application.process_update(make_update(application, "newqr"))
    assert sent[-1] == "Введите название книги:"
    await application.process_update(make_update(application, "New Book"))
    conn = sqlite3.connect(tmp / "test.db")
    qr = conn.execute("SELECT qr_code FROM books WHERE qr_code='newqr'").fetchone()
    conn.close()
    assert qr[0] == "newqr"
    # non-admin attempt
    await application.process_update(make_update(application, "/start", user_id=2))
    await application.process_update(make_update(application, "User", user_id=2))
    await application.process_update(make_update(application, "U", user_id=2))
    await application.process_update(make_update(application, "Main", user_id=2))
    await application.process_update(
        make_update(application, "➕ Добавить книгу", user_id=2)
    )
    assert sent[-1] == "Недостаточно прав."


@pytest.mark.asyncio
async def test_change_office(app):
    application, sent, tmp = app
    # register user
    await application.process_update(make_update(application, "/start"))
    await application.process_update(make_update(application, "Last"))
    await application.process_update(make_update(application, "First"))
    await application.process_update(make_update(application, "Main"))

    await application.process_update(make_update(application, "🏢 Сменить офис"))
    assert sent[-1] == "Выберите офис:"
    await application.process_update(make_update(application, "Alt"))
    conn = sqlite3.connect(tmp / "test.db")
    office = conn.execute("SELECT office FROM users WHERE telegram_id=1").fetchone()[0]
    conn.close()
    assert office == "Alt"


@pytest.mark.asyncio
async def test_take_book_photo(app, monkeypatch):
    application, sent, tmp = app
    await application.process_update(make_update(application, "/start"))
    await application.process_update(make_update(application, "Last"))
    await application.process_update(make_update(application, "First"))
    await application.process_update(make_update(application, "Main"))

    utils.save_book(
        {
            "qr_code": "qr1",
            "title": "Book",
            "status": "available",
            "taken_by": None,
            "taken_date": None,
            "office": "Main",
        }
    )

    import qrcode
    import io

    img = qrcode.make("qr1")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    class FakeFile:
        def __init__(self, data):
            self.data = data

        async def download_as_bytearray(self, *args, **kwargs):
            return bytearray(self.data)

    async def fake_get_file(self, file_id, *args, **kwargs):
        return FakeFile(data)

    monkeypatch.setattr(application.bot.__class__, "get_file", fake_get_file)

    await application.process_update(make_update(application, "🔍 Взять книгу"))
    assert sent[-1] == "Отправьте QR-код книги:"

    await application.process_update(make_photo_update(application))
    assert any("успешно" in m for m in sent[-2:])


@pytest.mark.asyncio
async def test_add_book_photo(app, monkeypatch):
    application, sent, tmp = app
    # admin registration
    await application.process_update(make_update(application, "/start", user_id=1))
    await application.process_update(make_update(application, "Admin"))
    await application.process_update(make_update(application, "User"))
    await application.process_update(make_update(application, "Main"))

    import qrcode
    import io

    img = qrcode.make("photoqr")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    class FakeFile:
        def __init__(self, data):
            self.data = data

        async def download_as_bytearray(self, *args, **kwargs):
            return bytearray(self.data)

    async def fake_get_file(self, file_id, *args, **kwargs):
        return FakeFile(data)

    monkeypatch.setattr(application.bot.__class__, "get_file", fake_get_file)

    await application.process_update(make_update(application, "➕ Добавить книгу"))
    assert sent[-1] == "Отправьте QR-код новой книги:"

    await application.process_update(make_photo_update(application))
    assert sent[-1] == "Введите название книги:"

    await application.process_update(make_update(application, "Photo Book"))
    conn = sqlite3.connect(tmp / "test.db")
    row = conn.execute(
        "SELECT qr_code, title FROM books WHERE qr_code='photoqr'"
    ).fetchone()
    conn.close()
    assert row[0] == "photoqr"
    assert row[1] == "Photo Book"
