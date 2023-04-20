import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (ApiAnswerError,
                        TokensError)

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

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if not PRACTICUM_TOKEN:
        logging.critical(
            ('Отсутствует токен PRACTICUM_TOKEN. '
             'Бот не может продолжить работу.')
        )
        raise ValueError(
            ('Отсутствует токен PRACTICUM_TOKEN. '
             'Бот не может продолжить работу.')
        )
    if not TELEGRAM_TOKEN:
        logging.critical(
            ('Не задан TELEGRAM_TOKEN.')
        )
        raise ValueError(
            ('Не задан TELEGRAM_TOKEN.')
        )
    if not TELEGRAM_CHAT_ID:
        logging.critical(
            ('Не задан TELEGRAM_CHAT_ID.')
        )
        raise ValueError(
            ('Не задан TELEGRAM_CHAT_ID.')
        )
    return True


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
            ('Ошибка отправки сообщения '
             '"{message}" в Telegram: {error}').format(
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
    logging.debug('Ответ API получен.')
    return response_json


def check_response(response: dict) -> list:
    """Проверяет ответ API на соответствие документации."""
    logging.debug('Проводим проверки ответа API.')
    if not isinstance(response, dict):
        raise TypeError(f'Ответ содержит не словарь, а {type(response)}.')
    if 'homeworks' not in response:
        raise KeyError(
            'Отсутствует ключ homeworks.'
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(f'Ответ содержит не словарь, а {type(homeworks)}.')
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
        raise ValueError(f'Неизвестный статус работы - {status}'
                         )
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[status]
    logging.debug('Информация о статусе работы получена.')
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise TokensError()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    current_report = {
        'name': '',
        'message': ''
    }
    prev_report = current_report.copy()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                current_report['name'] = homework['homework_name']
                current_report['message'] = parse_status(homework)
            else:
                current_report['message'] = 'Нет новых статусов'
            if current_report != prev_report:
                if send_message(bot, current_report['message']):
                    prev_report = current_report.copy()
                    current_timestamp = response.get(
                        'current_date', current_timestamp)
            else:
                logger.debug('Нет новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['message'] = message
            logger.exception(message)
            if current_report != prev_report:
                send_message(bot, str(error))
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
