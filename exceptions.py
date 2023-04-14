class ApiAnswerError(Exception):
    """Ошибка ответа API."""
    pass


class ApiAnswerErrorKey(Exception):
    """В ответе API найдены ключи, сообщающие об ошибке."""
    pass