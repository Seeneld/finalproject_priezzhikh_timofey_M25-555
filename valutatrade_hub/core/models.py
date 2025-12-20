import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional


class User:
    """Представляет пользователя системы"""
    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None
    ) -> None:
        self.user_id = user_id
        self.username = username
        if salt is None:
            salt = secrets.token_urlsafe(16)
        self._salt = salt
        self.hashed_password = self._hash_password(password)
        if registration_date is None:
            registration_date = datetime.now()
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = value

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Хеш пароля должен быть строкой")
        self._hashed_password = value

    @property
    def _salt(self) -> str:
        return self.__salt

    @_salt.setter
    def _salt(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Соль должна быть строкой")
        self.__salt = value

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с солью с использованием SHA256"""
        if len(password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов")
        return hashlib.sha256((password + self.__salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли введённый пароль с хранимым хешем"""
        return self._hash_password(password) == self._hashed_password

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя"""
        self.hashed_password = self._hash_password(new_password)

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе (без пароля)"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }


class Wallet:
    """Кошелёк для одной валюты"""
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты должен быть непустой строкой")
        self.currency_code = currency_code.strip().upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополние баланса"""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным числом")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        """Снимает средства, если достаточно баланса"""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом")
        if amount > self._balance:
            raise ValueError("Недостаточно средств на балансе")
        self._balance -= amount

    def get_balance_info(self) -> dict:
        """Возвращает информацию о балансе кошелька"""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }


class Portfolio:
    """Портфель пользователя"""
    def __init__(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        # Возврат копии, чтобы предотвратить прямое изменение извне
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """Добавление нового кошелька для указанной валюты, если его ещё нет"""
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты должен быть непустой строкой")
        code = currency_code.strip().upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует")
        self._wallets[code] = Wallet(code)

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возврат кошелька по коду валюты"""
        code = currency_code.strip().upper()
        if code not in self._wallets:
            raise KeyError(f"Кошелёк для валюты {code} не найден")
        return self._wallets[code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Возврат общей стоимости портфеля в базовой валюте"""
        # Фиксированные курсы относительно USD
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.07,
            "RUB": 0.011,
            "BTC": 90000.0,
            "ETH": 5000.0,
        }

        base = base_currency.upper()
        if base not in exchange_rates:
            raise ValueError(f"Базовая валюта не поддерживается: {base}")

        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
            elif code in exchange_rates:
                usd_value = wallet.balance * exchange_rates[code]
                total += usd_value / exchange_rates[base]
            else:
                # Игнорируем валюты с неизвестным курсом
                pass
        return round(total, 2)