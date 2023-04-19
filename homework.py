import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (ApiAnswerError,
                        ApiAnswerErrorKey)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTIC_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

TOKENS = [
    'PRACTICUM_TOKEN',
    'TELEGRAM_TOKEN',
    'TELEGRAM_CHAT_ID',
]


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logging.debug('Проверка наличия всех токенов.')
    none_tokens = [token_name for token_name
                   in TOKENS if globals()[token_name] is None]
    if none_tokens:
        logging.critical(
            ('Отсутствует токен_ы {none_tokens}. '
             'Бот не может продолжить работу.').format(
                none_tokens=none_tokens
            )
        )
        raise ValueError(
            ('Список недоступных токенов: '
                '{none_tokens}.').format(
                none_tokens=none_tokens
            )
        )


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info(('Начало отправки сообщения '
                      '"{message}" в Telegram').format(message=message)
                     )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(
            ('Сообщениe "{message}" '
             'отправлено в Telegram.').format(
                message=message
            )
        )
    except telegram.error.TelegramError as error:
        logging.exception(
            ('Сообщениe "{message}" отправлено в Telegram.').format(
                message=message,
                error=error
            )
        )


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса Яндекс."""
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        response = requests.get(**params_request)
    except requests.RequestException as error:
        raise ConnectionError(
            ('Ошибка запроса к API: {error}. '
             'Параметры запроса: {params_request}').format(
                error=error,
                params_request=params_request
            )
        )
    if response.status_code != 200:
        raise ApiAnswerError(
            ('Не удалось получить ответ API. '
             'Код полученного ответа: {status_code}. '
              'Параметры запроса: {params_request}').format(
                status_code=response.status_code,
                params_request=params_request
            )
        )
    response_json = response.json()
    for error_key in ['error', 'code']:
        if error_key in response_json:
            raise ApiAnswerErrorKey(
                ('Отказ сервера. В ответе сервера найден ключ: '
                 '{error_key}. Ошибка: {error}. '
                  'Параметры запроса: {params_request}').format(
                    error_key=error_key,
                    error=response_json[error_key],
                    params_request=params_request
                )
            )
    logging.debug('Ответ API получен.')
    return response_json


def check_response(response: dict) -> list:
    """Проверяет ответ API на соответствие документации."""
    logging.debug('Проводим проверки ответа API.')
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ содержит не словарь, а {type}.'.format(
                type=type(response)
            )
        )
    if 'homeworks' not in response:
        raise KeyError(
            'Отсутствует ключ homeworks.'
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            'homeworks является не списком, а {type}.'.format(
                type=type(homeworks)
            )
        )
    logging.debug('Ответ API содержит список homeworks.')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(
            'Отсутствует ключ homework_name.'
        )
    if 'status' not in homework:
        raise KeyError(
            'Отсутствует ключ status.'
        )
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            'Неизвестный статус работы - {status}'.format(
                status=status
            )
        )
    logging.debug('Информация о статусе работы получена.')
    return (
        ('Изменился статус проверки работы '
         '"{homework_name}". {verdict}').format(
            homework_name=homework.get('homework_name'),
            verdict=HOMEWORK_VERDICTS[status]
        )
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    logging.info('Бот начал работу.')
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Нет новых статусов.')
                continue
            message = parse_status(homeworks[0])
            if last_message != message:
                send_message(bot, message)
                logging.debug('Бот успешно отправил статус в Telegram.')
                last_message = message
                timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = 'Сбой в работе программы: {error}'.format(
                error=error
            )
            logging.exception(message)
            if last_message != message:
                try:
                    send_message(bot, message)
                    last_message = message
                except Exception as error:
                    logging.exception(
                        ('Ошибка отправки сообщения '
                         '"{message}" в Telegram: {error}').format(
                            message=message, error=error
                        )
                    )
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(
                filename=__file__ + '.log', mode='w', encoding='UTF-8'),
            logging.StreamHandler(stream=sys.stdout)
        ],
        format='%(asctime)s, %(levelname)s, %(funcName)s, '
               '%(lineno)s, %(message)s',
    )
    main()
