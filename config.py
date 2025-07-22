"""Configuration for the Telegram bot loaded from environment variables."""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


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
    "NaSemenovskoy": {"admins": _office_admins("NaSemenovskoy")},
    # ООО «БитРу», пл. Семёновская, 1а, 11 этаж БЦ «Соколиная Гора"
    # Используется короткое имя SokolGora
    "SokolGora": {"admins": _office_admins("SokolGora")},
    # Офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32, 3 этаж
    "Bolshaya32": {"admins": _office_admins("Bolshaya32")},
    # Центральный офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32/7, 2 этаж
    "Central": {"admins": _office_admins("Central")},
    # IT-Технопарк «ФизТехПарк» – Москва, ш. Долгопрудненское, д. 3
    "FizTechPark": {"admins": _office_admins("FizTechPark")},
    # Курорт «ЕРИНО» – поселок Ерино, микрорайон Санаторий, д. 1, стр. 5
    "Erino": {"admins": _office_admins("Erino")},
    # ООО «Открытые мастерские» – Москва, ул. Электрозаводская, д. 27, стр. 8
    "OpenWorkshops": {"admins": _office_admins("OpenWorkshops")},
    # Проектный офис ГК «ОСНОВА» – Москва, ул. Электрозаводская, д. 27, стр. 2
    "ProjectOffice": {"admins": _office_admins("ProjectOffice")},
}
