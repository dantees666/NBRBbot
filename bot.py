import config
import telebot
from telebot import types

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['go', 'start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item5 = types.KeyboardButton("Часто задаваемые вопросы")
    item4 = types.KeyboardButton("Как записаться на экскурсию?")
    item3 = types.KeyboardButton("Приложения")
    item2 = types.KeyboardButton("Мероприятия")
    item1 = types.KeyboardButton('О нас')

    markup.add(item1, item2, item3, item4, item5)

    bot.send_message(message.chat.id,
                     "Добро пожаловать, {0.first_name}!\n\nЯ - <b>{1.first_name}</b>, бот Национальной Библиотеки Республики Бурятия, "
                     "создан для того, "
                     "чтобы рассказать вам о возможностях нашей библиотеки,"
                     "просто узнать что-то о нас или зарегистрироваться удаленно.\n".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=markup)

    # Обработчик текстовых сообщений
    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        if message.text == "Как записаться на экскурсию?":
            bot.send_message(
                message.chat.id,
                "Вы можете записаться на экскурсию в регистрационной, на входе в библиотеку.\n\n"
                "Также можно записаться по [ссылке](https://iframeab-pre6061.intickets.ru/event/12331186).",
                parse_mode='Markdown'
            )

        elif message.text == "Часто задаваемые вопросы":
            bot.send_message(
                message.chat.id,
                "📚 <b>Часто задаваемые вопросы:</b>\n\n"
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
                "Ксерокопия, презентации, экспертизы книг.\n",
                parse_mode='html'
            )


# RUN
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except ConnectionError as e:
        print('Ошибка соединения: ', e)
    except Exception as r:
        print("Непридвиденная ошибка: ", r)
    finally:
        print("Здесь всё закончилось")