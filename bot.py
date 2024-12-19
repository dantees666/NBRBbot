import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import telebot
from aiosmtplib import SMTP
from fuzzywuzzy import fuzz
from telebot import types
import config
import re

bot = telebot.TeleBot(config.token)

# Данные для отправки email
EMAIL_HOST = "smtp.mail.ru"
EMAIL_PORT = 465
EMAIL_USER = "tumen95@bk.ru" # Почта с которой отправляется сообщение
EMAIL_PASS = "***********" # Специальный пароль для приложения (создаётся в личном кабинете эмэйл!)
EMAIL_TO = "tumen95@bk.ru" # Почта на которую приходят сообщения

# Словарь вопросов и ответов с синонимами
FAQ_ANSWERS = {
    "о нас": {
        "answer": "📖 <b>Национальная библиотека Республики Бурятия</b> — центр знаний, культуры и инноваций.\n\n"
                  "Адрес: Улан-Удэ, ул. Ленина, 50.\n"
                  "Часы работы: Пн-Пт с 9:00 до 18:00, Сб с 10:00 до 17:00, Вс — выходной.\n\n"
                  "Подробнее на <a href='https://nbrb.ru/'>нашем сайте</a>.",
        "synonyms": ["о нас", "что это за библиотека", "расскажите о библиотеке"]
    },
    "часы работы": {
        "answer": "📅 <b>Часы работы библиотеки:</b>\n\n"
                  "Пн-Пт: с 9:00 до 18:00\n"
                  "Сб: с 10:00 до 17:00\n"
                  "Вс: выходной.\n\n"
                  "Приходите в любое удобное для вас время!",
        "synonyms": ["часы работы", "во сколько открывается библиотека", "до скольки работает библиотека",
                     "время работы библиотеки", "когда работает библиотека"]
    },
    "мероприятия": {
        "answer": "🎉 <b>Наши мероприятия:</b>\n\n"
                  "📅 Лекции, мастер-классы, презентации книг, репетиции хора и многое другое.\n\n"
                  "📌 Следите за афишей на <a href='https://nbrbru.tmweb.ru/affiche/'>нашем сайте</a>.",
        "synonyms": ["мероприятия", "какие мероприятия проходят", "что происходит в библиотеке"]
    },
    "экскурсия": {
        "answer": "🚶‍♂️ <b>Как записаться на экскурсию?</b>\n\n"
                  "Запись возможна на стойке регистрации или онлайн по "
                  "<a href='https://iframeab-pre6061.intickets.ru/event/12331186'>ссылке</a>.",
        "synonyms": ["экскурсия", "как записаться на экскурсию", "запись на экскурсию"]
    },
    "часто задаваемые вопросы": {
        "answer": "📚 <b>Часто задаваемые вопросы:</b>\n\n"
                  "1. <b>Кто может записаться?</b> \n"
                  "Граждане РФ и иностранцы старше 14 лет с паспортом.\n\n"
                  "2. <b>Как записаться?</b>\n"
                  "Лично на стойке регистрации или через Госуслуги. "
                  "<a href='https://nbrbru.tmweb.ru/info/kak-zapisatsa/'>Подробнее</a>\n\n"
                  "3. <b>Что можно делать с читательским билетом?</b>\n"
                  "Брать книги, пользоваться ресурсами, работать за ПК.\n\n"
                  "4. <b>Как заказать книги?</b>\n"
                  "В электронном каталоге (требуется читательский билет). "
                  "<a href='http://nbrbru.tmweb.ru/info/kak-zakazat-knigu/'>Подробнее</a>\n\n"
                  "5. <b>Как продлить книги?</b>\n"
                  "До 5 книг на 15 дней, можно продлить 2 раза. "
                  "<a href='http://nbrbru.tmweb.ru/info/kak-prodlit-knigu'>Подробнее</a>\n\n"
                  "6. <b>Что можно без билета?</b>\n"
                  "Посетить мероприятия, экскурсии, купить книги.\n\n"
                  "7. <b>Дополнительные услуги:</b>\n"
                  "Ксерокопия, презентации, экспертизы книг.",
        "synonyms": ["часто задаваемые вопросы", "вопрос", "задать вопрос", "книги", "Без билета", "Заказать"]
    }
}
# Временное хранилище для данных пользователей
user_data = {}

# Список доступных тем для сообщения
EMAIL_SUBJECTS = ["Вопрос библиотекарю", "Вопрос по абонементу", "Вопрос по книгам", "Вопрос о мероприятиях",
                  "Техническая поддержка"]

# Регулярные выражения для проверки ввода телефона и email
PHONE_REGEX = r"^\+?[78][0-9]{10}$"  # Российский номер телефона (7, 8 или +7 и 10 цифр)
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"  # Стандартная проверка email
LIBRARY_CART_REGEX = r"^[0-9]{6}$"  # Номер читательского билета библиотеки (6 цифр)


# Функция для поиска похожих запросов
def get_closest_match(user_input):
    best_match, highest_score = None, 0
    for key, data in FAQ_ANSWERS.items():
        for synonym in data["synonyms"]:
            similarity = fuzz.partial_ratio(user_input.lower(), synonym.lower())
            if similarity > highest_score:
                best_match, highest_score = key, similarity
    return best_match if highest_score > 60 else None  # Порог совпадения


# Асинхронная отправка email
async def send_email_async(name, phone, email, city, subject, message, library_card):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject  # Выбранная пользователем тему письма
        body = (f"<b>Имя:</b> {name}<br><b>Телефон:</b> {phone}<br><b>Email:</b> {email}<br>"
                f"<b>Город:</b> {city}<br><b>Сообщение:</b> {message}<br><b>Читательский билет:</b> {library_card}")
        msg.attach(MIMEText(body, "html", "utf-8"))

        async with SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=True) as smtp_client:
            await smtp_client.login(EMAIL_USER, EMAIL_PASS)
            await smtp_client.send_message(msg)
    except Exception as e:
        print(f"Ошибка отправки email: {e}")


def add_interrupt_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Прервать (Задать вопрос библиотекарю)")
    return markup


# Стартовое сообщение
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("О нас", "Мероприятия", "Как записаться на экскурсию?")
    markup.add("Часто задаваемые вопросы", "Задать вопрос библиотекарю")
    bot.send_message(
        message.chat.id,
        f"Добро пожаловать, {message.from_user.first_name}! Выберите интересующий вас пункт в меню 👇",
        reply_markup=markup,
    )


# Обработка текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    if user_id in user_data and user_data[user_id].get("step"):
        process_dialog(message)
        return

    if message.text == "Задать вопрос библиотекарю":
        description = (
            "Спросить библиотекаря — Национальная библиотека РБ\n\n"
            "Что можно запросить бесплатно:\n"
            "- Список литературы (до 10 наименований) и ссылки на источники.\n"
            "- Уточнение данных о книгах, местонахождении изданий в библиотеке.\n"
            "- Консультации по работе отделов библиотеки.\n\n"
            "Платные услуги:\n"
            "- Сканирование статей (но не книг полностью).\n"
            "- Списки литературы более 10 наименований.\n"
            "- Копирование электронных документов на носители.\n"
            "- Отправка документов по электронной почте.\n\n"
            "Что библиотека не делает:\n"
            "- Не решает задачи по точным наукам.\n"
            "- Не пишет за вас рефераты, курсовые, дипломы.\n"
            "- Не ищет информацию о родственниках и истории населённых пунктов.\n"
            "- Не предоставляет полные электронные версии книг (только в здании библиотеки).\n\n"
            "Как задать вопрос:\n"
            "- Заполнить форму, выбрать тематику и отправить запрос.\n"
            "- Ответ приходит в течение 1-3 рабочих дней.\n\n"
            "Лимиты:\n"
            "- Не более 3 запросов в день от одного пользователя.\n\n"
            "Часы работы:\n"
            "- Онлайн-запросы принимаются ежедневно, кроме выходных и праздников (время Улан-Удэ, UTC+9)."
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Написать сообщение", "Не писать")
        bot.send_message(user_id, description, reply_markup=markup)
    elif message.text == "Написать сообщение":
        user_data[user_id] = {"step": "name"}
        bot.send_message(user_id, "Как к вам обращаться:", reply_markup=add_interrupt_buttons())
    else:
        user_input = message.text.strip()
        match = get_closest_match(user_input)
        if match:
            bot.send_message(user_id, FAQ_ANSWERS[match]["answer"], parse_mode='html')
        else:
            bot.send_message(user_id, "🤔 Я не понял ваш запрос. Попробуйте уточнить вопрос.")


# Обработка этапов диалога
def process_dialog(message):
    user_id = message.chat.id
    user = user_data.setdefault(user_id, {})
    step = user.get("step")

    if message.text == "Прервать":
        user_data.pop(user_id, None)
        bot.send_message(user_id, "Диалог прерван. Чем ещё могу помочь?", reply_markup=add_interrupt_buttons())
        return

    if step == "name":
        user["name"] = message.text
        user["step"] = "subject"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for subject in EMAIL_SUBJECTS:
            markup.add(subject)
        bot.send_message(user_id, "Выберите тему вашего вопроса:", reply_markup=markup)

    elif step == "subject":
        if message.text in EMAIL_SUBJECTS:
            user["subject"] = message.text
            user["step"] = "phone"
            bot.send_message(user_id, "Введите ваш телефон:", reply_markup=add_interrupt_buttons())
        else:
            bot.send_message(user_id, "Пожалуйста, выберите тему из предложенных вариантов.")

    elif step == "phone":
        if re.match(PHONE_REGEX, message.text):
            user["phone"] = message.text
            user["step"] = "has_library_card"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Да", "Нет")
            bot.send_message(user_id, "Есть ли у вас читательский билет?", reply_markup=markup)
        else:
            bot.send_message(user_id,
                             "🚫 Неверный формат телефона. Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX.")

    elif step == "has_library_card":
        if message.text.lower() == "да":
            user["step"] = "library_card"
            bot.send_message(user_id, "Введите номер читательского билета (6 цифр):",
                             reply_markup=add_interrupt_buttons())
        else:
            user["step"] = "email"
            bot.send_message(user_id, "Введите ваш E-mail:", reply_markup=add_interrupt_buttons())

    elif step == "library_card":
        if re.match(LIBRARY_CART_REGEX, message.text):
            user["library_card"] = message.text
            user["step"] = "email"
            bot.send_message(user_id, "Введите ваш E-mail:", reply_markup=add_interrupt_buttons())
        else:
            bot.send_message(user_id, "🚫 Номер читательского билета должен состоять из 6 цифр. Попробуйте снова.")

    elif step == "email":
        if re.match(EMAIL_REGEX, message.text):
            user["email"] = message.text
            user["step"] = "city"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Пропустить")
            bot.send_message(user_id, "Введите ваш город (по желанию):", reply_markup=markup)
        else:
            bot.send_message(user_id, "🚫 Неверный формат E-mail. Убедитесь, что адрес введён правильно.")

    elif step == "city":
        user["city"] = message.text
        user["step"] = "message"
        bot.send_message(user_id, "Введите ваше сообщение:", reply_markup=add_interrupt_buttons())


    elif step == "message":
        user["message"] = message.text
        data = user_data.pop(user_id, {})

        asyncio.run(send_email_async(
            data.get("name"),
            data.get("phone"),
            data.get("email"),
            data.get("city", 'Не указан'),
            data.get("subject", 'Вопрос библиотекарю'),
            data.get("message"),
            data.get("library_card", 'Не указан')
        ))

        bot.send_message(user_id, "✅ Спасибо! Ваш вопрос отправлен.")

# Запуск бота
if __name__ == "__main__":
    bot.infinity_polling()