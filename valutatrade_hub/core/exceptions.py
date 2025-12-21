class InsufficientFundsError(Exception):
    """Исключение: недостаточно средств на кошельке"""
    def __init__(self, available: float, required: float, code: str) -> None:
        self.available = available
        self.required = required
        self.code = code
        message = f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Исключение: валюта с указанным кодом не поддерживается"""
    def __init__(self, code: str) -> None:
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Исключение: ошибка при обращении к внешнему API"""
    def __init__(self, reason: str) -> None:
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)

class UserError(Exception):
    """Исключение, вызываемое при ошибках, связанных с пользователем"""
    pass
