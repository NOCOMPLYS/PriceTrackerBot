import requests
from fake_useragent import UserAgent


def processing(silk):
    """
    Функция проверяет полученную строку на то, является ли она ссылкой на товар на одном из
    указанных сайтов

    :param silk: Строка
    :return: Строка с названием магазина
    :return: -1 в случае ошибки
    """
    if silk.startswith("https://www"):
        response = requests.get(silk, headers={'User-Agent': UserAgent().chrome})  # Отправка запроса сайту
        if response.status_code != 200:  # Статус 200 состояния HTTP значит, что получен ответ от сервера
            return -1
        if "https://www.mvideo.ru/products/" in silk:
            return "mvideo"
        elif "https://www.dns-shop.ru/product/" in silk:
            return "dns"
        elif "https://www.ozon.ru/product/" in silk:
            return "ozon"
        elif "https://www.citilink.ru/product/" in silk or "https://www.citilink.ru/amp/product/" in silk:
            return "citilink"
        elif "https://www.eldorado.ru/cat/detail/" in silk:
            return "eldorado"
        else:
            return -1
    else:
        return -1
