"""Configuration for the Telegram bot loaded from environment variables."""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

# Ensure environment variables are loaded when the application is started from
# any working directory. We look for a ``.env`` file located next to this module
# (i.e. in the project root) and load it if present.
base_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(base_dir, ".env")
example_path = os.path.join(base_dir, ".env.example")

# Load variables from .env if present. If not, fall back to .env.example so the
# bot can run with the example configuration out of the box.
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
elif os.path.exists(example_path):
    load_dotenv(example_path)


def _parse_ids(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))

# Offices available for registration. Keys are the office names that will be
# presented to the user during the /start flow. Each office can optionally
# define administrators specific to that office. Administrator IDs can be
# provided via environment variables using the pattern
# ``OFFICE_<OFFICE_NAME>_ADMINS`` where ``OFFICE_NAME`` is uppercase.


def _office_admins(name: str) -> List[str]:
    env_var = f"OFFICE_{name.upper()}_ADMINS"
    return _parse_ids(os.getenv(env_var, ""))


OFFICES = {
    # Офис ГК «ОСНОВА» – Москва, ул. Малая Семёновская, д. 9, стр. 3, 2 этаж
    "NaSemenovskoy": {
        "name": "На Семёновской",
        "admins": _office_admins("NaSemenovskoy"),
    },
    # ООО «БитРу», пл. Семёновская, 1а, 11 этаж БЦ «Соколиная Гора"
    # Используется короткое имя SokolGora
    "SokolGora": {
        "name": "Соколиная Гора",
        "admins": _office_admins("SokolGora"),
    },
    # Офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32, 3 этаж
    "Bolshaya32": {
        "name": "Большая 32",
        "admins": _office_admins("Bolshaya32"),
    },
    # Центральный офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32/7, 2 этаж
    "Central": {
        "name": "Центральный",
        "admins": _office_admins("Central"),
    },
    # IT-Технопарк «ФизТехПарк» – Москва, ш. Долгопрудненское, д. 3
    "FizTechPark": {
        "name": "ФизТехПарк",
        "admins": _office_admins("FizTechPark"),
    },
    # Курорт «ЕРИНО» – поселок Ерино, микрорайон Санаторий, д. 1, стр. 5
    "Erino": {
        "name": "Ерино",
        "admins": _office_admins("Erino"),
    },
    # ООО «Открытые мастерские» – Москва, ул. Электрозаводская, д. 27, стр. 8
    "OpenWorkshops": {
        "name": "Открытые мастерские",
        "admins": _office_admins("OpenWorkshops"),
    },
    # Проектный офис ГК «ОСНОВА» – Москва, ул. Электрозаводская, д. 27, стр. 2
    "ProjectOffice": {
        "name": "Проектный офис",
        "admins": _office_admins("ProjectOffice"),
    },
}
