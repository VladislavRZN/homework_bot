LOG_DEBUG_START_CHECK_TOKENS = 'Проверка наличия всех токенов.'
LOG_CRITICAL_CHECK_TOKENS = ('Отсутствует токен_ы {none_tokens}. '
                             'Бот не может продолжить работу.')
NONE_TOKENS_ERROR_CHECK_TOKENS = ('Список недоступных токенов: '
                                  '{none_tokens}.')
LOG_INFO_START_SEND_MESSAGE = ('Начало отправки сообщения '
                               '"{message}" в Telegram')
LOG_DEBAG_SEND_MESSAGE = ('Сообщениe "{message}" '
                          'отправлено в Telegram.')
LOG_EXCEPT_SEND_MESSAGE = ('Ошибка отправки сообщения '
                           '"{message}" в Telegram: {error}')
TELEGRAM_ERROR_SEND_MESSAGE = ('Ошибка отправки сообщения '
                               'в Telegram: {error}')
CONNECTION_ERROR_GET_API_ANSWER = 'Ошибка соединения: {error}.'
REQUEST_EXCEPTION_GET_API_ANSWER = ('Ошибка запроса к API: {error}. '
                                    'Параметры запроса: {params_request}')
HTTP_NOT_OK_ERROR_GET_API_ANSWER = ('Не удалось получить ответ API. '
                                    'Код полученного ответа: {status_code}. '
                                    'Параметры запроса: {params_request}')
RESPONSE_ERROR_GET_API_MESSAGE = ('Отказ сервера. В ответе сервера найден ключ: '
                                  '{error_key}. Ошибка: {error}. '
                                  'Параметры запроса: {params_request}')
LOG_DEBAG_GET_API_ANSWER = 'Ответ API получен.'
LOG_INFO_START_CHECK_RESPONSE = 'Проводим проверки ответа API.'
NOT_DICT_ERROR_CHECK_RESPONSE = 'Ответ содержит не словарь, а {type}.'
HOMEWORKS_KEY_ERROR_CHECK_RESPONSE = 'Отсутствует ключ homeworks.'
NOT_LIST_ERROR_CHECK_RESPONSE = 'homeworks является не списком, а {type}.'
LOG_DEBAG_CHECK_RESPONSE = 'Ответ API содержит список homeworks.'
HOMEWORK_NAME_KEY_ERROR_PARSE_STATUS = 'Отсутствует ключ homework_name.'
STATUS_NAME_KEY_ERROR_PARSE_STATUS = 'Отсутствует ключ status.'
MESSAGE_PARSE_STATUS = ('Изменился статус проверки работы '
                        '"{homework_name}". {verdict}')
STATUS_ERROR_PARSE_STATUS = 'Неизвестный статус работы - {status}'
LOG_DEBAG_PARSE_STATUS = 'Информация о статусе работы получена.'
LOG_INFO_MAIN = 'Бот начал работу.'
LOG_DEBUG_MAIN = 'Бот успешно отправил статус в Telegram.'
LOG_DEBUG_NO_STATUS_MAIN = 'Нет новых статусов.'
MAIN_ERROR_MESSAGE = 'Сбой в работе программы: {error}'