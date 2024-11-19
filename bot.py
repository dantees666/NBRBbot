import config
import telebot
from telebot import types
from fuzzywuzzy import fuzz

bot = telebot.TeleBot(config.token)

FAQ_ANSWERS = {
    "о нас": "📖 <b>Национальная библиотека Республики Бурятия</b> — центр знаний, культуры и инноваций.\n\n"
             "Адрес: Улан-Удэ, ул. Ленина, 50.\n"
             "Часы работы: Пн-Пт с 9:00 до 18:00, Сб с 10:00 до 17:00, Вс — выходной.\n\n"
             "Подробнее на <a href='https://nbrb.ru/'>нашем сайте</a>.",
    "мероприятия": "🎉 <b>Наши мероприятия:</b>\n\n"
                   "📅 Лекции, мастер-классы, презентации книг, репетиции хора и многое другое.\n\n"
                   "📌 Следите за афишей на <a href='https://nbrbru.tmweb.ru/affiche/'>нашем сайте</a> "
                   "или в социальных сетях.\n\n"
                   "🔖 На некоторые события можно попасть по Пушкинской карте.",
    "экскурсия": "🚶‍♂️ <b>Как записаться на экскурсию?</b>\n\n"
                 "Вы можете записаться на экскурсию в регистрационной зоне библиотеки или онлайн по "
                 "<a href='https://iframeab-pre6061.intickets.ru/event/12331186'>ссылке</a>.\n\n"
                 "Экскурсии проходят с понедельника по четверг каждую неделю.",
    "часто задаваемые вопросы": "📚 <b>Часто задаваемые вопросы:</b>\n\n"
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
                                 "Ксерокопия, презентации, экспертизы книг."
}

def get_closest_match(user_input):
    best_match = None
    highest_score = 0
    for question in FAQ_ANSWERS:
        similarity = fuzz.partial_ratio(user_input.lower(), question.lower())
        if similarity > highest_score:
            best_match = question
            highest_score = similarity
    return best_match if highest_score > 60 else None  # Порог 60% для "похожести"


# Команда /start
@bot.message_handler(commands=['go', 'start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item5 = types.KeyboardButton("Часто задаваемые вопросы")
    item4 = types.KeyboardButton("Как записаться на экскурсию?")
    item2 = types.KeyboardButton("Мероприятия")
    item1 = types.KeyboardButton("О нас")

    markup.add(item1, item2, item4, item5)

    bot.send_message(
        message.chat.id,
        f"Добро пожаловать, {message.from_user.first_name}!\n\n"
        f"Я - <b>{bot.get_me().first_name}</b>, бот Национальной Библиотеки Республики Бурятия.\n\n"
        "Я помогу вам узнать о возможностях нашей библиотеки, "
        "посмотреть мероприятия или зарегистрироваться на экскурсии.\n\n"
        "Выберите интересующий вас пункт в меню 👇",
        parse_mode='html', reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_input = message.text.strip()
    match = get_closest_match(user_input)

    if match:
        bot.send_message(
            message.chat.id,
            FAQ_ANSWERS[match],
            parse_mode='html'
        )
    else:
        bot.send_message(
            message.chat.id,
            "🤔 Извините, я не понял ваш запрос. Попробуйте переформулировать вопрос или выберите пункт из меню."
        )

# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except ConnectionError as e:
        print('Ошибка соединения: ', e)
    except Exception as r:
        print("Непредвиденная ошибка: ", r)
    finally:
        print("Завершение работы бота.")
