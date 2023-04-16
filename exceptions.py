class ClassWorkError(Exception):
    pass


class HTTPRequestError(ClassWorkError):
    def __init__(self, response):
        message = (
            f'Эндпоинт {response.url} недоступен. '
            f'Код ответа API: {response.status_code}'
        )
        super().__init__(message)


class ParseStatusError(ClassWorkError):
    def __init__(self, text):
        message = (
            f'Парсинг ответа API: {text}'
        )
        super().__init__(message)


class CheckResponseError(ClassWorkError):
    def __init__(self, text):
        message = (
            f'Проверка ответа API: {text}'
        )
        super().__init__(message)


class NotSendMessageTelegram(ClassWorkError):
    def __init__(self):
        message = (
            'Ошибка при отправке сообщения в телеграм.'
        )
        super().__init__(message)