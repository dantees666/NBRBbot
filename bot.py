import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import telebot
from aiosmtplib import SMTP
from fuzzywuzzy import fuzz
from telebot import types
import config

bot = telebot.TeleBot(config.token)

# Данные для отправки email
EMAIL_HOST = "smtp.mail.ru"      # SMTP-сервер для Mail.ru
EMAIL_PORT = 465                 # Порт SMTP
EMAIL_USER = "library_email@mail.ru"  # Почта библиотеки
EMAIL_PASS = "your_password"         # Пароль почты библиотеки
EMAIL_TO = "library_email@mail.ru"   # Адрес библиотеки

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
        "synonyms": ["часто задаваемые вопросы", "вопрос", "задать вопрос"]
    }
}
# Временное хранилище для данных пользователей
user_data = {}

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
async def send_email_async(name, phone, email, city, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO
        msg["Subject"] = "Вопрос библиотекарю"
        body = f"<b>Имя:</b> {name}<br><b>Телефон:</b> {phone}<br><b>Email:</b> {email}<br>" \
               f"<b>Город:</b> {city}<br><b>Сообщение:</b> {message}"
        msg.attach(MIMEText(body, "html", "utf-8"))
        smtp_client = SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT, use_tls=True)
        async with smtp_client:
            await smtp_client.login(EMAIL_USER, EMAIL_PASS)
            await smtp_client.send_message(msg)
    except Exception as e:
        print(f"Ошибка отправки email: {e}")

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
    if user_id in user_data and "step" in user_data[user_id]:
        process_dialog(message)
        return

    if message.text == "Задать вопрос библиотекарю":
        user_data[user_id] = {"step": "name"}
        bot.send_message(user_id, "Введите ваше имя:")
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
    step = user_data[user_id]["step"]

    if step == "name":
        user_data[user_id]["name"] = message.text
        user_data[user_id]["step"] = "phone"
        bot.send_message(user_id, "Введите ваш телефон:")
    elif step == "phone":
        user_data[user_id]["phone"] = message.text
        user_data[user_id]["step"] = "email"
        bot.send_message(user_id, "Введите ваш E-mail:")
    elif step == "email":
        user_data[user_id]["email"] = message.text
        user_data[user_id]["step"] = "city"
        bot.send_message(user_id, "Введите ваш город (по желанию):")
    elif step == "city":
        user_data[user_id]["city"] = message.text
        user_data[user_id]["step"] = "message"
        bot.send_message(user_id, "Введите ваше сообщение:")
    elif step == "message":
        user_data[user_id]["message"] = message.text
        data = user_data.pop(user_id)  # Удаляем данные после отправки
        asyncio.create_task(
            send_email_async(data["name"], data["phone"], data["email"], data["city"], data["message"])
        )
        bot.send_message(user_id, "✅ Спасибо! Ваш вопрос отправлен. Мы свяжемся с вами в ближайшее время.")

# Запуск бота
if __name__ == "__main__":
    bot.infinity_polling()