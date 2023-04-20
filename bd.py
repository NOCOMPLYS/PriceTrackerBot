import csv
import parsing
import pandas as pd
import os
import json
from datetime import date


def getFilename(user):
    """
    Получаем название файла базы данных конкретного пользователя

    :param user: идентификатор пользователя
    """

    return 'Database_' + str(user) + '.csv'


def CheckUserCSV(user):
    """
    Проверяем существует ли файл базы данных конкретного пользователя

    :param user: идентификатор пользователя
    """

    if os.path.exists(getFilename(user)):
        return True
    else:
        return False


def CheckSameURL(user, URL):
    """
    Проверяем, записан ли такой товар в базе данных пользователя,
    сверяя переданную ссылку со всеми значениями столбца 'URL'

    :param user: идентификатор пользователя
    :param URL: ссылка на товар
    """

    # Проверка на существование файла БД
    if not CheckUserCSV(user):
        return False

    df = pd.read_csv(getFilename(user), index_col='URL', encoding='windows_1251')
    if URL in df.index:
        return True
    else:
        return False


def CreateCSV(user):
    """
    Создание файла базы данных конкретного пользователя, заполнение основных заголовков

    :param user: идентификатор пользователя
    """

    with open(getFilename(user), 'w') as csvfile:
        fieldnames = ['Product', 'Store', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    csvfile.close()


def SaveInCSV(user, product, store, URL):
    """
    Сохранение товара в базу данных конкретного пользователя.

    При сохранении товара, заполняются основные сведения о нём
    (Имя товара, магазин, в котором товар отслеживается и ссылка на товар в этом магазине).

    После этого при помощи парсинга получаем актуальную цену товара и записываем в столбец,
    заголовком которого будет актуальная дата.

    :param user: идентификатор пользователя
    :param product: имя товара
    :param store: магазин, в котором необходимо отслеживать товар
    :param URL: ссылка на товар
    """

    # Создание БД, если её не существует
    if not CheckUserCSV(user):
        CreateCSV(user)

    # Проверка, на наличие такого товара в БД
    if CheckSameURL(user, URL):
        return 1

    # Запись основной информации о товаре в БД
    with open(getFilename(user), 'a') as csvfile:
        fieldnames = ['Product', 'Store', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'Product': product, 'Store': store, 'URL': URL})
    csvfile.close()

    # Преобразование файла БД в словарь
    database = []  # Словарь, в который будет записана информация из БД
    with open(getFilename(user), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            database.append(row)
    csvfile.close()

    price = parsing.parse(URL, store)  # Парсинг цены
    AddCurPrice(user, len(database) - 1, price)  # Запись цены в столбец с актуальной датой


def DeleteFromCSV(user, index):
    """
    Удаление товара из файла базы данных по номеру

    :param user: идентификатор пользователя
    :param index: номер товара, который необходимо удалить
    """

    # Проверка на существование файла БД
    if not CheckUserCSV(user):
        return 2

    # Запись информации из файла БД в pandas DataFrame
    df = pd.read_csv(getFilename(user), engine='python', encoding='windows_1251')

    # Проверка, на то, что такой товар действительно существует в БД
    # if product not in df.index:
    #     return 1

    df.drop(index=[index], inplace=True)
    df.to_csv(getFilename(user), encoding='windows_1251', index=False)


def AddCurPrice(user, index, price):
    """
    Добавление цены в столбец с сегодняшней датой в строку под номером index.
    В случае, если такого столбца не существует он создастя автоматически.

    :param user: идентификатор пользователя
    :param index: номер строки, для которой необходимо записать цену
    :param price: значение цены, которое необходимо записать в БД
    """

    # Проверка на существование файла БД
    if not CheckUserCSV(user):
        return 1

    df = pd.read_csv(getFilename(user), engine='python', encoding='windows_1251')
    df.at[index, str(date.today())] = price
    df.to_csv(getFilename(user), index=False, encoding='windows_1251')


def getUserList(user):
    """
    Получение имени товара, ссылки на товар, а также последней записанной цены из файла БД.
    Данные сохраняются в формате двумерного массива для каждой строки в файле, кроме строки заголовков.

    :param user: идентификатор пользователя
    """

    # Проверка на существование товара
    if not CheckUserCSV(user):
        return []

    df = pd.read_csv(getFilename(user), usecols=['Product', 'URL', str(date.today())], encoding='windows_1251')
    dataframe = df.to_numpy()
    return dataframe


def UpdateAll():
    """
    Данная функция запускает функцию обновления цен для всех файлов баз данных пользователей.
    Идентификаторы пользователей получаем из файла Users.
    """

    with open('Users', 'r') as files:
        db_list = json.load(files)
    files.close()

    for user in db_list:
        if CheckUserCSV(user):  # Проверка на существование файла данного пользователя
            UpdateDB(user)


def UpdateDB(user):
    """
    Данная функция получает актуальную цену каждого товара для одного конкретного файла базы данных
    и записывает её в столбец с актуальной датой.

    :param user: идентификатор пользователя
    """

    # Преобразование файла БД в словарь
    database = []  # Словарь, в который будет записана информация из БД
    with open(getFilename(user), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            database.append(row)
    csvfile.close()

    # Построчная запись актуальной цены в столбец с актуальной датой
    for i in range(len(database)):
        price = parsing.parse(database[i]['URL'], database[i]['Store'])
        AddCurPrice(user, i, price)
