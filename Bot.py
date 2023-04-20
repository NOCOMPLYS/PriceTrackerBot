import json
from aiogram.utils.exceptions import BotBlocked
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ChatActions
import bd
import urlcheck
import asyncio
import aioschedule


# Присваивание переменной TOKEN строки с токеном бота, полученным у @BotFather (в целях безопасности токен,
# использовавшийся для теста программы удалён, для теста необходимо самостоятельно получить токен у @BotFather)
TOKEN = ""

# Создание объекта бота bot с помощью функции Bot() сторонней библиотеки aiogram и передача ему переменнной TOKEN
# в качестве параметра token
bot = Bot(token=TOKEN)

# Создание объекта диспетчера dp с помощью функции Discpatcher() сторонней библиотеки aiogram
# и передача ему переменной bot в качестве параметра bot
dp = Dispatcher(bot=bot)


# Открытие и чтение массива, хранящегося в файле Users.json и содержащего id пользователей, использовавших бота ранее
with open('Users', 'r') as file:
    from_json = json.load(file)  # массив с id пользователей записывается в переменную from_json
file.close()


"""
 Словарь диалоговых состояний - словарь, в котором ключом является id пользователя, а значением - True/False
 Словари диалоговых состояний необходимы для определения того, как бот должен реагировать на сообщение пользователя
 если оно не является командой
"""

# Создание пустых словарей диалоговых состояний naming_products, adding_products и deleting_products:
# 1 - Словарь naming_products отображает, ожидает ли бот от пользователя название нового продукта
# 2 - Словарь adding_products отображает, производит ли бот парсинг товара и сохранение его в CSV файл пользователя
# 2 - Словарь deleting_products отображает, ожидает ли бот от пользователя номер удаляемого товара
naming_products = {}
adding_products = {}
deleting_products = {}

# Создание пустых словарей shops и urls:
# 1 - Словарь urls хранит последнюю корректную ссылку, присланною пользователем для дальнейшей обработки, ключом для
#     каждой ссылки служит id пользователя
# 2 - Словарь shops хранит название магазина, на который ведёт последняя корректная ссылка, присланная пользователем,
#     ключом для каждого названия является id пользователя
urls = {}
shops = {}

# Присваивание ключу, являющемуся id каждого пользователя, ранее использовавшего бота, значения False в словарях
# naming_products, adding_products и deleting_products
for user in from_json:
    naming_products[user] = False
    adding_products[user] = False
    deleting_products[user] = False


async def update():
    """
    Функция запускает обновление цен всех отслеживающихся товаров во всех БД с помощью функции
    UpdateAll(), описанной в файле bd.py

    :return: Функция ничего не возвращает
    """
    bd.UpdateAll()


async def scheduler():
    """
    Функция реализует метод планировки операций ввода/вывода I/O Scheduling
    За счёт своей асинхронности функция позволяет программе работать в многопоточном режиме

    :return:
    """
    aioschedule.every().day.at("00:00").do(update)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    """
    Функция запускает сопрограмму(задание) sheduler(), тем самым реализуя многопоточность и позволяя
    обновлять все цены во всех базах данных раз в сутки в установленное время в автоматическом режиме
    В моменты, когда программа не совершает никаких других действий, функция проверяет условия выполнения,
    указанные в scheduler и в случае совпадения - запускает её

    :param _:
    :return:
    """
    asyncio.create_task(scheduler())


async def load_animation(message: types.Message):
    """
    Функция отправляет пользователю сообщения, уведомляющие о начале поиска файла и добавления последнего в базу данных
    Далее функция отправляет строку, состоящую из 10 белых квадратов, после редактирет это сообщения, поочерёдно заменяя
    слева направо белые квадраты зелёными с интервалом в 0.3 секунды, тем самым имитируя загрузку
    В конце своей работы функция отправляет сообщение, уведомляющее о скором завершении обработки запроса пользователя

    :param message: Объект типа Message сторонней библиотеки aiogram - сообщение пользователя
    :return: Функция ничего не возвращает
    """
    await bot.send_message(message.from_user.id,
                           "🔄Отлично! Ищу цену товара и добавляю его в отслеживаемые, это может занять некоторое время...")
    upload_message = await bot.send_message(chat_id=message.from_user.id, text="⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️")
    await asyncio.sleep(1)

    # Цикл, в котором происходит редактирование сообщения с интервалом 0.3 секунды
    for i in range(1, 11):
        await upload_message.edit_text(text="🟩" * i + (10 - i) * "⬜️")
        await asyncio.sleep(0.3)
    await bot.send_message(message.from_user.id, "🔄Почти готово...")


# Хэндлер, ответственный за обработку сообщения с командой /start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """
    Функция достаёт массив с id пользователей, уже использовавших бота, из файла User.json, проверяет наличие id
    пользователя в этом массиве, в случае отсутствия - добавляет id в массив и загружает его назад в Users.json

    Так же функция добавляет/изменяет(в случае если пользоваетль уже использовал бота) все диалоговые состояния
    пользователя на False

    :param message: Объект типа Message сторонней библиотеки aiogram - сообщение пользователя
    :return: Функция ничего не возвращает
    """
    # Достаём масив, содержащий id пользователей из файла Users.json
    with open('Users', 'r') as file:
        users = json.load(file)
    file.close()

    # Если id пользователя отсутствует в массиве в файле Users.json, он добавлятся в этот массив
    if message.from_user.id not in users:

        # Запись пользователя в массив в файле Users.json
        with open('Users', 'w') as file:
            users.append(message.from_user.id)
            json.dump(users, file)
        file.close()

    # Присваивание ключу, являющемуся id пользователя значения False в словарях naming_products, adding_products
    # и deleting_products
    naming_products[message.from_user.id] = False
    deleting_products[message.from_user.id] = False
    adding_products[message.from_user.id] = False

    await bot.send_message(message.from_user.id, "ℹ️Я бот, предназначенный для ведения базы данных CSV с текущими ценами интересующих тебя товаров в следующих магазинах: Ситилинк, Днс, Эльдорадо, Мвидео и Озон\n\n🕛Пришли мне ссылку на товар, я проверю его стоимость и занесу в базу данных. Дальше я буду проверять цены на отслеживаемые товары раз в сутки в 00.00 UTC+3 и обновлять их в твоей базе данных\n\n🗂Ты можешь запросить CSV-файл с отслеживаемыми товарами и их ценами в любое удобное время\n\n📎Пришли ссылку, чтобы начать отслеживать цену товара", reply_markup=menu)


# Хэндлер, ответственный за обработку сообщения с командой /doarickroll
@dp.message_handler(commands=['doarickroll'])
async def rickroller(msg: types.Message):
    """
    Функция отправляет пользователю сообщение со старой, но навевающей воспоминания шуткой

    :param msg: Объект типа Message сторонней библиотеки aiogram - сообщение пользователя
    :return: функция возвращает пользователя во времена лампового интернета, Медведа и Упячки
    """
    await bot.send_message(msg.from_user.id, '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">Never gonna give you up\nNever gonna let you down\nNever gonna run around and desert you\nNever gonna make you cry\nNever gonna say goodbye\nNever gonna tell a lie and hurt you</a>', parse_mode="HTML")


@dp.message_handler(commands=['update'])
async def updater(msg: types.Message):
    """
    Функция предназначена для ручного обновления всех БД администраторами
    :param msg:
    :return:
    """
    if msg.from_user.id == 276194719 or msg.from_user.id == 73318898:
        await bot.send_message(msg.from_user.id, "Приветствую, администратор!\n\nЗапускаю обновление всех БД в ручном режиме")
        await bot.send_message(276194719,
                               "ℹ️Администратор запустил обновление БД в ручном режиме")
        await bot.send_message(73318898,
                               "ℹ️Администратор запустил обновление БД в ручном режиме")
        bd.UpdateAll()
        await bot.send_message(276194719,
                               "✅Завершено обновление всех БД")
        await bot.send_message(73318898,
                               "✅Завершено обновление всех БД")


# Хэндлер, обрабатывающий сообщения, не являющиеся командами
@dp.message_handler()
async def no_type_message(msg: types.Message):
    """
    Работу функции можно разделить на обработку текста сообщений, отправка которых вызвана нажатием встроенных кнопок
    и сообщений неизвестного содержания

    В случае, если пользовательское сообщение - текст встроенной кнопки, сообщение будет обработано соответственно тому,
    какая кнопка была выбрана

    В противном случае в зависимости от диалогового состояния пользователя, сообщение будет расценено либо как
    ссылка на товар, либо как название добавляемого товара, либо как номер удаляемого товара в списке и будет обработано
    соответствующимм образом

    :param msg: Объект типа Message сторонней библиотеки aiogram - сообщение пользователя
    :return: 0 - если пользователь присылает любое сообщение во время парсинга и сохранения
             информации о товаре в базу данных
    """

    # Призваивание переменной user значение id пользователя для дальнейшега удобства в использовании
    user = msg.from_user.id

    # Проверка на то, производится ли парсинг и сохранение информации о товаре в базу данных пользователя
    if adding_products[user] is True:
        return 0

    # Обработка текста сообщения, присылаемого встроенной кнопкой "➕Добавление товара"
    if msg.text == "➕Добавление товара":

        await bot.send_message(user, "📎Пришли мне ссылку на товар и я начну отслеживать информацию о нём и заносить в твой CSV-файл\n\nℹ️Тебе необязательно нажимать на эту кнопку каждый раз, ты можешь просто присылать мне ссылку и я сам всё пойму")

    # Обработка текста сообщения, присылаемого встроенной кнопкой "🗂Получить свой CSV-файл"
    elif msg.text == "🗂Получить свой CSV-файл":

        # Присваивание переменной file_name имени файла пользователя с помощью функции getFilename(),
        # описанной в файле bd.py
        file_name = bd.getFilename(user)

        # Присваивание переменной products двумерного массива, содержащего имена и url сайтов и цены товаров из
        # CSV файла пользователя с помощью функции getUserList(), описанной в файле bd.py
        products = bd.getUserList(user)

        # Если у пользователя сейчас есть хотя бы один отслеживаемый товар
        if len(products) != 0:

            await bot.send_message(user, "📌Прикрепил твой CSV-файл ниже:")

            #Открытие CSV файла пользователя, отправка файла, закрытие файла
            file_for_user = open(file_name, 'rb')
            await bot.send_chat_action(user, ChatActions.UPLOAD_DOCUMENT)
            await bot.send_document(user, file_for_user)
            file_for_user.close()

        else:
            await bot.send_message(user, "Ты пока не отслеживаешь ни один товар\n\n📎Пришли мне ссылку на товар и я начну отслеживать информацию о нём и заносить в твой CSV-файл")

    # Обработка текста сообщения, присылаемого встроенной кнопкой "➖Удаление товара"
    elif msg.text == "➖Удаление товара":

        # Если у пользователя сейчас есть хотя бы один отслеживаемый товар
        if len(bd.getUserList(user)) != 0:

            # Присваивание пользовательскому id значения True в словаре диалоговых состояний deleting_products,
            # что означает переключение бота в режим ожидания номера удаляемого товара от пользователя
            deleting_products[user] = True
            await bot.send_message(user, 'Пришли мне номер товара, который ты хочешь удалить\n\nℹ️Номер товара можно узнать, нажав кнопку "Список товаров"')

        else:
            await bot.send_message(user,
                                   "Ты пока не отслеживаешь ни один товар\n\n📎Пришли мне ссылку на товар и я начну отслеживать информацию о нём и заносить в твой CSV-файл")

    # Обработка текста сообщения, присылаемого встроенной кнопкой "📋Список товаров"
    elif msg.text == "📋Список товаров":

        # Присваивание переменной products двумерного массива, содержащего имена и url сайтов и цены товаров из
        # CSV файла пользователя с помощью функции getUserList(), описанной в файле bd.py
        products = bd.getUserList(user)

        # Если у пользователя сейчас есть хотя бы один отслеживаемый товар
        if len(products) != 0:

            output = '📋Вот список товаров, которые ты отслеживаешь:\n\n'

            # Цикл, в котором производится формирование сообщения в переменной output, адресованного пользователю
            # и содержащего номер товара, его название(являющееся гиперссылкой на сам товар) и цену в рублях
            product_index = 1
            for product, url, price in products:
                output += str(product_index) + '. ' + '<a href=' + '"' + url + '">' + product + '</a>' + ' - ' + str(price)
                if price == 'Parsing Error' or price == 'Товар временно отсутствует в продаже':
                    output += '\n'
                else:
                    output += '₽' + '\n'
                product_index += 1
            output += '\n'

            await bot.send_message(user, output, parse_mode="HTML")

        else:
            await bot.send_message(user, "Ты пока не отслеживаешь ни один товар\n\n📎Пришли мне ссылку на товар и я начну отслеживать информацию о нём и заносить в твой CSV-файл")

    # Если текст сообщения не является ни командой ни текстом встроенных кнопопок
    else:
        # Если пользователь прислал не название добавляемого товара и не номер удаляемого товара означает,
        # что пользователь прислал ссылку на товар
        if naming_products[user] is False and deleting_products[user] is False:

            # Присваивание переменной url текста сообщения пользователя
            url = msg.text

            # Присваивание переменной shop_name значения, полученного с помощью функции processing(),
            # описанной в файле urlcheck.py
            # Значение - название магазина, в случае корректности ссылки, -1 - в противном случае
            shop_name = urlcheck.processing(url)

            # Если ссылка, присланная пользователем корректна
            if shop_name != -1:

                # Если ссылка, присланная пользователем не указывает на уже отслеживаемый товар
                # Проверка осуществляется с помощью функции CheckSameURL(), описанной в файле bd.py
                if bd.CheckSameURL(user, url) is False:

                    # Сохранение ссылки пользователя в словарь urls по ключу, представляющему id пользователя
                    urls[user] = url

                    # Сохранение названия магазина, указанного в ссылке пользователя в словарь urls
                    # по ключу, представляющему id пользователя
                    shops[user] = shop_name

                    await bot.send_message(user,
                                           "Теперь пришли мне название, под которым товар будет записан в базе данных")

                    # Присваивание пользовательскому id значения True в словаре диалоговых состояний naming_products,
                    # что означает переключение бота в режим ожидания названия нового товара
                    naming_products[user] = True

                else:
                    await bot.send_message(user, "🚫Товар, находящийся по этой ссылке уже отслеживается")
            else:
                await bot.send_message(user, "🚫Ссылка, которую ты прислал некорректна, попробуй ещё раз")

        # Если бот находится в режиме ожидания названия нового товара от пользователя
        elif naming_products[user] is True:

            # Отключение режима ожидания названия нового товара от пользователя
            naming_products[user] = False

            # Присваивание пользовательскому id значения True в словаре диалоговых состояний adding_products,
            # что означает переключение бота в режим парсинга и работы с бд
            # Этот режим необходим чтобы пользователь не мог послать запрос боту пока тот парсит и работает с БД
            adding_products[user] = True

            # Проигрывание анимации с помощью функции load_animation()
            await load_animation(msg)

            #
            bd.SaveInCSV(user, msg.text, shops[user], urls[user])

            # Удаление последних ссылки и названия магазина, добавленных пользователем из словарей
            # shops и urls
            del shops[msg.from_user.id], urls[msg.from_user.id]

            await bot.send_message(user, "✅Добавил товар в твою базу данных")

            # Отключение режима парсинга и работы с бд
            adding_products[user] = False

        # Если бот находится в режиме ожидания номера удаляемого продукта от пользователя
        elif deleting_products[user] is True:

            # Присваивание переменной products двумерного массива, содержащего имена и url сайтов и цены товаров из
            # CSV файла пользователя с помощью функции getUserList(), описанной в файле bd.py
            products = bd.getUserList(user)

            # Если у пользователя сейчас есть хотя бы один отслеживаемый товар
            if len(products) != 0:

                # Проверка номера продукта в списке, введённого пользователем, на корректность
                if '1' <= msg.text <= str(len(products)):

                    # Удаление товара из БД с помощью функции DeleteFromCSV, описанной в файле bd.DeleteFromCSV
                    bd.DeleteFromCSV(user, int(msg.text) - 1)

                    await bot.send_message(user, '✅Удалил товар из твоей базы данных')
                else:
                    await bot.send_message(user, 'Упс! Товара с таким номером нет в твоей базе данных\n\n📋Нажми кнопку "Список товаров", чтобы увидеть номер нужного тебе товара и возвращайся сюда')
            else:
                await bot.send_message(user,
                                       "Ты пока не отслеживаешь ни один товар\n\n📎Пришли мне ссылку на товар и я начну отслеживать информацию о нём и заносить в твой CSV-файл")

            # Отключение режима ожидания номера удаляемого товара от пользователя
            deleting_products[user] = False


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    """
    Функция обрабатывает исключение, возникающее при блокировке пользователем бота во время его работы

    :param update: Объект типа Update сторонней библиотеки aiogram
    :param exception: Объект типа BotBlocked сторонней библиотеки aiogram
    :return: True во всех случаях
    """

    # Вывод в консоль сообщения о произошедшей блокировкой пользователем бота
    print(f"Меня заблокировал пользователь!\nСообщение: {update}\nОшибка: {exception}")

    return True


# ----Меню----
# Создание четырёх объектов кнопок меню с помощью функции KeyboardButton() сторонней библиотеки aiogram
add_url_button = KeyboardButton("➕Добавление товара")
delete_product_button = KeyboardButton("➖Удаление товара")
recieve_csv_button = KeyboardButton("🗂Получить свой CSV-файл")
show_products_list_button = KeyboardButton("📋Список товаров")

# Создание меню встроенных кнопок с помощью функции ReplyKeyboardMarkup() сторонней библиотеки aiogram
menu = ReplyKeyboardMarkup(resize_keyboard=True).add(add_url_button, delete_product_button, show_products_list_button, recieve_csv_button)

# Запуск бота с помощью функции start_polling() сторонней библиотеки aiogram
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
