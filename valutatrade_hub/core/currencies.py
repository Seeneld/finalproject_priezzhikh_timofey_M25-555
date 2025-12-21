from abc import ABC, abstractmethod
import re
from typing import Dict


class CurrencyNotFoundError(Exception):
    """Исключение, вызываемое при отсутствии валюты с указанным кодом"""
    pass


class Currency(ABC):
    """Абстрактный базовый класс валюты"""

    def __init__(self, name: str, code: str) -> None:
        self.name = name
        self.code = code

    @property
    def name(self) -> str:
        """Отображаемое имя валюты"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя валюты не может быть пустым")
        self._name = value.strip()

    @property
    def code(self) -> str:
        """Код валюты"""
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Код валюты должен быть строкой")
        clean_value = value.strip().upper()
        if not clean_value:
            raise ValueError("Код валюты не может быть пустым")
        if not (2 <= len(clean_value) <= 5):
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if not re.match(r"^[A-Z0-9]+$", clean_value):
            raise ValueError("Код валюты может содержать только буквы и цифры")
        self._code = clean_value

    @abstractmethod
    def get_display_info(self) -> str:
        """Форматированное представление валюты для логов"""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта, эмитируемая государством или зоной"""

    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)
        self.issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Страна или зона эмиссии"""
        return self._issuing_country

    @issuing_country.setter
    def issuing_country(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Страна эмиссии не может быть пустой")
        self._issuing_country = value.strip()

    def get_display_info(self) -> str:
        """Форматированное отображение фиатной валюты"""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self._issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта с алгоритмом и рыночной капитализацией"""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float) -> None:
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Алгоритм консенсуса"""
        return self._algorithm

    @algorithm.setter
    def algorithm(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Алгоритм не может быть пустым")
        self._algorithm = value.strip()

    @property
    def market_cap(self) -> float:
        """Рыночная капитализация в USD"""
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Рыночная капитализация должна быть неотрицательным числом")
        self._market_cap = float(value)

    def get_display_info(self) -> str:
        """Форматированное отображение криптовалюты"""
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self._algorithm}, MCAP: {self._market_cap:.2e})"


# Реестр поддерживаемых валют
SUPPORTED_CURRENCIES: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russian Federation"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
}


def get_currency(code: str) -> Currency:
    """Получение объекта валюты по её коду"""
    code = code.strip().upper()
    if code not in SUPPORTED_CURRENCIES:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не поддерживается")
    return SUPPORTED_CURRENCIES[code]