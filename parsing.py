import requests
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from selenium import webdriver
from unipath import Path
import time
import lxml


# Функция открывает браузер Chrome, переходит по
# указанному url и парсит html-код страницы
# Принимает на вход строку с URL адресом сайта
# Возвращает объект, в котором хранится дерево html-кода
# либо -1 в случае, если был пойман Exception

def get_data_with_selenium(url):
    """
    Функция открывает браузер Chrome, переходит по
    указанному url и парсит html-код страницы

    :param url: Строка
    :return result: Объект, хранящий дерево html-кода страницы
    :return -1: В случае возникновения любого исключения
    """
    try:
        # Получение абсолютной ссылки на драйвер и её изменение под формат ссылок Windows
        path = Path("chromedriver.exe").absolute()   # Проверка на наличие драйвера
        absolute_path = ''
        for i in path:
            if ord(i) == 92:
                absolute_path += chr(92) * 2
            else:
                absolute_path += i
    except Exception as ex:
        print(ex)
        return -1

    chrome_options = webdriver.ChromeOptions()  # Добавление настроек запуска браузера
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    result = -1
    driver = -1

    try:
        driver = webdriver.Chrome(executable_path=path, options=chrome_options)  # Запуск драйвера
        driver.get(url=url)  # Получение доступа к сайту
        result = driver.page_source  # Сохранение html-кода страницы
        time.sleep(1)
    except Exception as ex:
        print(ex)
        return -1
    finally:
        if driver != -1:
            try:
                driver.close()  # Закрытие драйвера
            except Exception as ex:
                print(ex)
                return -1
            try:
                driver.quit()
            except Exception as ex:
                print(ex)
                return -1
            return result
        else:
            return -1

def parse(url, website_name):
    """
    Функция производит парсинг html-кода страницы и последующую обработку с целью получения цены товара

    :param url: Строка, ссылка на сайт
    :param website_name: Строка, имя сайта
    :return price: Число, цена товара (в случае успеха)
    :return 'Parsing Error': Строка (в случае возникновения исключений или необработанных вариантов)
    """
    responce = requests.get(url, headers={'User-Agent': UserAgent().chrome})  # Отправка запроса на сервер
    if responce.status_code != 200:  # Статус 200 состояния HTTP значит, что получен ответ от сервера
        print('Connection Error: ', responce.status_code)
        return -1
    else:
        # Разделение на разные методы обработки полученного html-кода в зависимости от сайта
        if website_name == 'citilink':
            silenium_result = get_data_with_selenium(url)  # Парсинг
            if silenium_result == -1:
                return -1
            soup = bs(silenium_result, 'lxml')
            result = soup.find_all('h2', class_='ProductHeader__not-available-header')  # Проверяем товар на наличие
            if result != []:
                return 'Товар временно отсутствует в продаже'
            else:
                try:
                    result = soup.find('span',
                                       class_='ProductHeader__price-default_current-price js--ProductHeader__price-default_current-price').text  # Ищем тег span с указанным классом
                except AttributeError:
                    return 'Parsing Error'
                price = ''
                for letter in result:
                    for i in str(letter):
                        if '0' <= i <= '9':
                            price += i
                if price == '':
                    price = 'Parsing Error'
                return price

        elif website_name == 'dns':
            silenium_result = get_data_with_selenium(url)  # Парсинг
            if silenium_result == -1:
                return -1
            soup = bs(silenium_result, 'lxml')
            try:
                result = eval(soup.find('script', type='application/ld+json').text)
                price = result['offers']['price']
                return price
            except AttributeError:
                try:
                    result = soup.find('div',
                                       class_='product-buy__price').text  # Ищем тег div с указанным классом
                except AttributeError:
                    return 'Товар временно отсутствует в продаже'
            price = ''
            for letter in result:
                for i in str(letter):
                    if '0' <= i <= '9':
                        price += i
            if price == '':
                price = 'Parsing Error'
            return price

        elif website_name == 'mvideo':
            silenium_result = get_data_with_selenium(url)  # Парсинг
            if silenium_result == -1:
                return -1
            soup = bs(silenium_result, 'lxml')
            result = soup.find_all('p', class_='product-sold-out-text')  # Проверяем товар на наличие
            if result != []:
                return 'Товар временно отсутствует в продаже'
            else:
                try:
                    result = soup.find('span', class_='price__main-value').text  # Ищем тег span с указанным классом
                except AttributeError:
                    return 'Parsing Error'
                price = ''
                for letter in result:  # Очищаем указанную цену от лишних символов
                    for i in str(letter):
                        if '0' <= i <= '9':
                            price += i
                if price == '':
                    price = 'Parsing Error'
                return price

        elif website_name == 'ozon':
            silenium_result = get_data_with_selenium(url)  # Парсинг
            if silenium_result == -1:
                return -1
            soup = bs(silenium_result, 'lxml')
            result = soup.find_all('h2', class_='e7z1')  # Проверяем товар на наличие
            if result != []:
                return 'Товар временно отсутствует в продаже'
            else:
                try:
                    result = soup.find('span', class_='c2h5').text  # Ищем тег span с указанным классом
                except AttributeError:
                    return 'Parsing Error'
                price = ''
                for letter in result:
                    for i in str(letter):
                        if '0' <= i <= '9':
                            price += i
                if price == '':
                    price = 'Parsing Error'
                return price

        elif website_name == 'eldorado':
            silenium_result = get_data_with_selenium(url)  # Парсинг
            if silenium_result == -1:
                return -1
            soup = bs(silenium_result, 'lxml')
            result = soup.find_all('script', type='text/javascript')  # Поиск скриптов типа 'text/javascript'

            result_text = ''
            for i in result:
                result_text += str(i)

            # Поиск переменной var dataLayer во всех полученных скриптах, содержащей словарь с ценой и наличием
            for i in range(len(result_text)):
                if result_text[i] == 'v' and result_text[i + 1] == 'a' and result_text[i + 2] == 'r' and \
                        result_text[i + 3] == ' ' and result_text[i + 4] == 'd' and result_text[i + 5] == 'a' and \
                            result_text[i + 6] == 't' and result_text[i + 7] == 'a' and result_text[i + 8] == 'L' and \
                                result_text[i + 9] == 'a' and result_text[i + 10] == 'y' and result_text[i + 11] == 'e' and \
                                    result_text[i + 12] == 'r' and result_text[i + 13] == ' ' and result_text[i + 14] == '=':

                    # Сохранение позиции начала словаря
                    position = i + 17
                    vocab = ''

                    # Проверка на окончание словаря
                    while result_text[position] != ']':
                        vocab += result_text[position]
                        position += 1

                    # Превращение полученного текста в словарь
                    vocab = eval(vocab)

                    try:
                        if vocab['productAvailability'] == 'not_available':
                            return 'Товар временно отсутствует в продаже'
                        else:
                            try:
                                price = vocab['ecommerce']['detail']['products']['price']
                            except Exception:
                                return 'Parsing Error'
                            return price
                    except Exception:
                        return 'Parsing Error'
