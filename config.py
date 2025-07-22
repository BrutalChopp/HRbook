BOT_TOKEN = "8155626371:AAFct2z_XvBaIfaYiNFdSnmuizPp9R0ITV4"
ADMIN_IDS = ["7007125219"]

# Offices available for registration. Keys are the office names that will be
# presented to the user during the /start flow. Each office can optionally
# define administrators specific to that office.
OFFICES = {
    # Офис ГК «ОСНОВА» – Москва, ул. Малая Семёновская, д. 9, стр. 3, 2 этаж
    "NaSemenovskoy": {"admins": []},
    # ООО «БитРу», пл. Семёновская, 1а, 11 этаж БЦ «Соколиная Гора»
    # Используется короткое имя SokolGora
    "SokolGora": {"admins": ["1000131763"]},
    # Офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32, 3 этаж
    "Bolshaya32": {"admins": []},
    # Центральный офис ГК «ОСНОВА» – Москва, ул. Большая Семёновская, д. 32/7, 2 этаж
    "Central": {"admins": []},
    # IT-Технопарк «ФизТехПарк» – Москва, ш. Долгопрудненское, д. 3
    "FizTechPark": {"admins": []},
    # Курорт «ЕРИНО» – поселок Ерино, микрорайон Санаторий, д. 1, стр. 5
    "Erino": {"admins": []},
    # ООО «Открытые мастерские» – Москва, ул. Электрозаводская, д. 27, стр. 8
    "OpenWorkshops": {"admins": []},
    # Проектный офис ГК «ОСНОВА» – Москва, ул. Электрозаводская, д. 27, стр. 2
    "ProjectOffice": {"admins": []},
}
