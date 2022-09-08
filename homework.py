import telegram
import time
import os
import logging
import requests
from dotenv import load_dotenv
import sys

load_dotenv

logging.basicConfig(
    filename='hw_logger.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в чат Телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception:
        logging.error('Не удалось отправить сообщение')


def get_api_answer(current_timestamp):
    """
    Делает запрос к API-серверу.
    В случае успеха возвращает ответ, преобразовав его к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logging.error(f'Ошибка запроса к серверу: {error}')
    if response.status_code != 200:
        logging.error('Сервер не отвечает, код ответа: {response.status_code}')
        raise Exception('Ошибка ответа сервера')
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на корректность.
    В случае успешного ответа возвращает список домашних работ.
    """
    if type(response) != dict:
        error_message = 'Некорректный ответ сервера'
        logging.error(error_message)
        raise TypeError(error_message)
    if 'homeworks' not in response:
        error_message = 'Ключ homeworks отсутствует'
        logging.error(error_message)
        raise KeyError(error_message)
    homeworks = response.get('homeworks')
    if type(homeworks) != list:
        error_message = 'homeworks не является списком'
        logging.error(error_message)
        raise TypeError(error_message)
    if len(homeworks) == 0:
        error_message = 'Пустой список домашних работ'
        logging.error(error_message)
        raise ValueError(error_message)
    homework = homeworks[0]
    return homework


def parse_status(homework):
    """Возвращает статус домашней работы."""
    if 'homework_name' not in homework:
        error_message = 'Ключ homework_name отсутствует'
        logging.error(error_message)
        raise KeyError(error_message)
    if 'status' not in homework:
        error_message = 'Ключ status отсутствует'
        logging.error(error_message)
        raise KeyError(error_message)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None or homework_status is None:
        return 'Работа не сдана на проверку'
    if homework_status not in HOMEWORK_STATUSES:
        error_message = 'Неизвестный статус домашней работы'
        logging.error(error_message)
        raise Exception(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for key, value in tokens.items():
        if value is None:
            logger.critical(f'Отсутствует переменная окружения {key}.')
            return False
        return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    send_message(bot, 'Привет!')

    while True:
        try:
            response = get_api_answer(current_timestamp)

            if response:
                homework = check_response(response)
                logging.info('Обновлен статус домашней работы')
                message = parse_status(homework)
                bot.send_message(TELEGRAM_CHAT_ID, message)

            current_timestamp = current_timestamp
            time.sleep(RETRY_TIME)

            if message:
                send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            bot.send_message(TELEGRAM_CHAT_ID, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
