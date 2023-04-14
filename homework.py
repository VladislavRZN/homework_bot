import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import text_messages
from exceptions import ApiAnswerError, ApiAnswerErrorKey

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
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
    """Проверка наличия всех токенов."""
    logging.debug(text_messages.LOG_DEBUG_START_CHECK_TOKENS)
    none_tokens = [token_name for token_name
                   in TOKENS if globals()[token_name] is None]
    if none_tokens:
        logging.critical(
            text_messages.LOG_CRITICAL_CHECK_TOKENS.format(
                none_tokens=none_tokens
            )
        )
        raise ValueError(
            text_messages.NONE_TOKENS_ERROR_CHECK_TOKENS.format(
                none_tokens=none_tokens
            )
        )


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        logging.info(
            text_messages.LOG_INFO_START_SEND_MESSAGE.format(
                message=message
            )
        )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(
            text_messages.LOG_DEBAG_SEND_MESSAGE.format(
                message=message
            )
        )
    except telegram.error.TelegramError as error:
        logging.exception(
            text_messages.LOG_EXCEPT_SEND_MESSAGE.format(
                message=message,
                error=error
            )
        )


def get_api_answer(timestamp):
    """Получение ответа от API."""
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        response = requests.get(**params_request)
    except requests.RequestException as error:
        raise ConnectionError(
            text_messages.REQUEST_EXCEPTION_GET_API_ANSWER.format(
                error=error,
                params_request=params_request
            )
        )
    if response.status_code != 200:
        raise ApiAnswerError(
            text_messages.HTTP_NOT_OK_ERROR_GET_API_ANSWER.format(
                status_code=response.status_code,
                params_request=params_request
            )
        )
    response_json = response.json()
    for error_key in ['error', 'code']:
        if error_key in response_json:
            raise ApiAnswerErrorKey(
                text_messages.RESPONSE_ERROR_GET_API_MESSAGE.format(
                    error_key=error_key,
                    error=response_json[error_key],
                    params_request=params_request
                )
            )
    logging.debug(text_messages.LOG_DEBAG_GET_API_ANSWER)
    return response_json


def check_response(response):
    """Проверка ответа."""
    logging.debug(text_messages.LOG_INFO_START_CHECK_RESPONSE)
    if not isinstance(response, dict):
        raise TypeError(
            text_messages.NOT_DICT_ERROR_CHECK_RESPONSE.format(
                type=type(response)
            )
        )
    if 'homeworks' not in response:
        raise KeyError(
            text_messages.HOMEWORKS_KEY_ERROR_CHECK_RESPONSE
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            text_messages.NOT_LIST_ERROR_CHECK_RESPONSE.format(
                type=type(homeworks)
            )
        )
    logging.debug(text_messages.LOG_DEBAG_CHECK_RESPONSE)
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(
            text_messages.HOMEWORK_NAME_KEY_ERROR_PARSE_STATUS
        )
    if 'status' not in homework:
        raise KeyError(
            text_messages.STATUS_NAME_KEY_ERROR_PARSE_STATUS
        )
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            text_messages.STATUS_ERROR_PARSE_STATUS.format(
                status=status
            )
        )
    logging.debug(text_messages.LOG_DEBAG_PARSE_STATUS)
    return (
        text_messages.MESSAGE_PARSE_STATUS.format(
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
    logging.info(text_messages.LOG_INFO_MAIN)
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug(text_messages.LOG_DEBUG_NO_STATUS_MAIN)
                continue
            message = parse_status(homeworks[0])
            if last_message != message:
                send_message(bot, message)
                logging.debug(text_messages.LOG_DEBUG_MAIN)
                last_message = message
                timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = text_messages.MAIN_ERROR_MESSAGE.format(
                error=error
            )
            logging.exception(message)
            if last_message != message:
                try:
                    send_message(bot, message)
                    last_message = message
                except Exception as error:
                    logging.exception(
                        text_messages.LOG_EXCEPT_SEND_MESSAGE.format(
                            message=message, error=error
                        )
                    )
        finally:
            time.sleep(RETRY_PERIOD)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Проверьте, заданы ли все токены')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != prev_message:
                    prev_message = message
                    send_message(bot, message)

        except ApiAnswerErrorKey:
            logging.error('Сбой при отправке сообщения в Telegram')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != prev_message:
                prev_message = message
                logging.error(message)
                send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()