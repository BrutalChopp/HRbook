import json
import pytest

from handlers.start import LAST_NAME, FIRST_NAME, OFFICE
import utils
from conftest import make_update


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
    data = json.loads((tmp / "users.json").read_text())
    assert data[0]["first_name"] == "Ivan"
    assert data[0]["office"] == "Main"


@pytest.mark.asyncio
async def test_take_and_return_book(app):
    application, sent, tmp = app
    # register user
    await application.process_update(make_update(application, "/start"))
    await application.process_update(make_update(application, "Last"))
    await application.process_update(make_update(application, "First"))
    await application.process_update(make_update(application, "Main"))
    # prepare book
    books = [
        {
            "qr_code": "qr1",
            "title": "Book",
            "status": "available",
            "taken_by": None,
            "taken_date": None,
            "office": "Main",
        }
    ]
    (tmp / "books.json").write_text(json.dumps(books), encoding="utf-8")
    # take book
    await application.process_update(make_update(application, "🔍 Взять книгу"))
    assert sent[-1] == "Отправьте QR-код книги:"
    await application.process_update(make_update(application, "qr1"))
    assert any("успешно" in m for m in sent[-2:])
    books = json.loads((tmp / "books.json").read_text())
    assert books[0]["status"] == "taken"
    # return book
    await application.process_update(make_update(application, "📤 Вернуть книгу"))
    assert sent[-1] == "Отправьте QR-код книги для возврата:"
    await application.process_update(make_update(application, "qr1"))
    books = json.loads((tmp / "books.json").read_text())
    assert books[0]["status"] == "available"


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
    books = json.loads((tmp / "books.json").read_text())
    assert books[0]["qr_code"] == "newqr"
    # non-admin attempt
    await application.process_update(make_update(application, "/start", user_id=2))
    await application.process_update(make_update(application, "User", user_id=2))
    await application.process_update(make_update(application, "U", user_id=2))
    await application.process_update(make_update(application, "Main", user_id=2))
    await application.process_update(
        make_update(application, "➕ Добавить книгу", user_id=2)
    )
    assert sent[-1] == "Недостаточно прав."
