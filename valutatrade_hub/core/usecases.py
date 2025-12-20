import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List

from valutatrade_hub.core.models import User
from valutatrade_hub.core import utils


class UserError(Exception):
    """Исключение, вызываемое при ошибках, связанных с пользователем"""
    pass


# Глобальная сессия
_current_user: Optional[User] = None


class UseCases:
    """Основной класс для бизнес-логики приложения"""

    def __init__(
        self,
        users_file: str = 'data/users.json',
        portfolios_file: str = 'data/portfolios.json',
        rates_file: str = 'data/rates.json'
    ) -> None:
        self.users_file = users_file
        self.portfolios_file = portfolios_file
        self.rates_file = rates_file
        self._ensure_data_files()

    def _ensure_data_files(self) -> None:
        """Создание файлов данных, если они отсутствуют"""

        # Инициализация users.json
        utils.ensure_file_exists(self.users_file, "[]")

        # Инициализация portfolios.json
        utils.ensure_file_exists(self.portfolios_file, "[]")

        # Инициализация rates.json
        initial_rates = {
            "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
            "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
            "RUB_USD": {"rate": 0.01016, "updated_at": datetime.now().isoformat()},
            "ETH_USD": {"rate": 3720.00, "updated_at": datetime.now().isoformat()},
            "source": "ParserService",
            "last_refresh": datetime.now().isoformat()
        }
        if not utils.file_exists(self.rates_file):
            utils.save_json_file(self.rates_file, initial_rates)

    def _load_users(self) -> List[Dict[str, Any]]:
        """Загрузка списка пользователей из файла"""
        return utils.load_json_file(self.users_file)

    def _save_users(self, users: List[Dict[str, Any]]) -> None:
        """Сохранение списка пользователей в файл"""
        utils.save_json_file(self.users_file, users)

    def _load_portfolios(self) -> List[Dict[str, Any]]:
        """Загрузка списка портфелей из файла"""
        return utils.load_json_file(self.portfolios_file)

    def _save_portfolios(self, portfolios: List[Dict[str, Any]]) -> None:
        """Сохранение списка портфелей в файл"""
        utils.save_json_file(self.portfolios_file, portfolios)

    def _load_rates(self) -> Dict[str, Any]:
        """Загрузка курсов валют из файла"""
        return utils.load_json_file(self.rates_file)

    def _save_rates(self, rates: Dict[str, Any]) -> None:
        """Сохранение курсов валют в файл"""
        utils.save_json_file(self.rates_file, rates)

    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя по имени"""
        users = self._load_users()
        for user in users:
            if user["username"] == username:
                return user
        return None

    def _get_portfolio_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение портфеля по ID пользователя"""
        portfolios = self._load_portfolios()
        for portfolio in portfolios:
            if portfolio["user_id"] == user_id:
                return portfolio
        return None

    def _save_portfolio_for_user(self, user_id: int, portfolio_dict: Dict[str, Any]) -> None:
        """Сохранение портфеля для пользователя"""
        portfolios = self._load_portfolios()
        for i, p in enumerate(portfolios):
            if p["user_id"] == user_id:
                portfolios[i] = portfolio_dict
                self._save_portfolios(portfolios)
                return
        portfolios.append(portfolio_dict)
        self._save_portfolios(portfolios)

    def _get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        """Расчёт курса из одной валюты в другую через USD"""
        rates = self._load_rates()
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        if from_curr == to_curr:
            return 1.0

        supported = ["USD", "EUR", "RUB", "BTC", "ETH"]
        if from_curr not in supported or to_curr not in supported:
            raise UserError(f"Курс {from_curr}->{to_curr} недоступен. Поддерживаемые валюты: {', '.join(supported)}")

        def to_usd(code: str, amount: float) -> float:
            if code == "USD":
                return amount
            pair = f"{code}_USD"
            if pair in rates:
                return amount * rates[pair]["rate"]
            raise UserError(f"Нет курса для {code} к USD")

        def from_usd(code: str, usd_amount: float) -> float:
            if code == "USD":
                return usd_amount
            pair = f"{code}_USD"
            if pair in rates:
                return usd_amount / rates[pair]["rate"]
            raise UserError(f"Нет курса от USD к {code}")

        usd_value = to_usd(from_curr, 1.0)
        return from_usd(to_curr, usd_value)

    def get_logged_in_user(self) -> User:
        """Получение текущего авторизованного пользователя"""
        if _current_user is None:
            raise UserError("Сначала выполните login")
        return _current_user

    def register_user(self, username: str, password: str) -> str:
        """Регистрация нового пользователя"""
        if len(password) < 4:
            raise UserError("Пароль должен быть не короче 4 символов")

        if self._get_user_by_username(username):
            raise UserError(f"Имя пользователя '{username}' уже занято")

        users = self._load_users()
        user_id = max([u["user_id"] for u in users], default=0) + 1
        salt = secrets.token_urlsafe(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()

        new_user = {
            "user_id": user_id,
            "username": username,
            "hashed_password": hashed,
            "salt": salt,
            "registration_date": datetime.now().isoformat()
        }
        users.append(new_user)
        self._save_users(users)

        # Создание пустого портфеля
        self._save_portfolio_for_user(user_id, {"user_id": user_id, "wallets": {}})

        return f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"

    def login_user(self, username: str, password: str) -> str:
        """Авторизация пользователя"""
        user_data = self._get_user_by_username(username)
        if not user_data:
            raise UserError(f"Пользователь '{username}' не найден")

        salt = user_data["salt"]
        hashed_input = hashlib.sha256((password + salt).encode()).hexdigest()
        if hashed_input != user_data["hashed_password"]:
            raise UserError("Неверный пароль")

        global _current_user
        _current_user = User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            password="dummy",
            salt=salt,
            registration_date=datetime.fromisoformat(user_data["registration_date"])
        )
        _current_user._hashed_password = user_data["hashed_password"]
        return f"Вы вошли как '{username}'"

    def show_portfolio(self, base: str = "USD") -> str:
        """Отображение портфеля пользователя с конвертацией в базовую валюту"""
        user = self.get_logged_in_user()
        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if not portfolio_data or not portfolio_data["wallets"]:
            return f"Портфель пользователя '{user.username}' пуст."

        base = base.upper()
        wallets = portfolio_data["wallets"]
        lines = []
        total_usd = 0.0

        for code, wallet in wallets.items():
            balance = wallet["balance"]
            if code == base:
                converted = balance
                usd_rate_base = self._get_exchange_rate(base, "USD") if base != "USD" else 1.0
                total_usd += balance * usd_rate_base
            else:
                try:
                    rate = self._get_exchange_rate(code, base)
                    converted = balance * rate
                    usd_rate = self._get_exchange_rate(code, "USD")
                    total_usd += balance * usd_rate
                except UserError:
                    converted = 0.0
            lines.append(f"- {code}: {balance:.4f} -> {converted:.2f} {base}")

        total_in_base = total_usd / (self._get_exchange_rate("USD", base) if base != "USD" else 1.0)

        result = f"Портфель пользователя '{user.username}' (база: {base}):\n"
        result += "\n".join(lines)
        result += f"\n{'-' * 33}\nИТОГО: {total_in_base:,.2f} {base}"
        return result

    def buy_currency(self, currency: str, amount: float) -> str:
        """Покупка валюты"""
        user = self.get_logged_in_user()
        if amount <= 0:
            raise UserError("'amount' должен быть положительным числом")
        currency = currency.upper().strip()
        if not currency:
            raise UserError("Код валюты не может быть пустым")

        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if currency not in portfolio_data["wallets"]:
            portfolio_data["wallets"][currency] = {"balance": 0.0}

        old_balance = portfolio_data["wallets"][currency]["balance"]
        portfolio_data["wallets"][currency]["balance"] = old_balance + amount
        self._save_portfolio_for_user(user.user_id, portfolio_data)

        try:
            rate = self._get_exchange_rate(currency, "USD")
            cost_usd = amount * rate
        except UserError:
            rate = None
            cost_usd = None

        result = f"Покупка выполнена: {amount:.4f} {currency}"
        if rate is not None:
            result += f" по курсу {rate:,.2f} USD/{currency}"
            result += f"\nОценочная стоимость покупки: {cost_usd:,.2f} USD"
        result += f"\nИзменения в портфеле:\n- {currency}: было {old_balance:.4f} -> стало {old_balance + amount:.4f}"
        return result

    def sell_currency(self, currency: str, amount: float) -> str:
        """Продажа валюты"""
        user = self.get_logged_in_user()
        if amount <= 0:
            raise UserError("'amount' должен быть положительным числом")
        currency = currency.upper().strip()
        if not currency:
            raise UserError("Код валюты не может быть пустым")

        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if currency not in portfolio_data["wallets"]:
            raise UserError(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")

        balance = portfolio_data["wallets"][currency]["balance"]
        if amount > balance:
            raise UserError(f"Недостаточно средств: доступно {balance:.4f} {currency}, требуется {amount:.4f} {currency}")

        old_balance = balance
        portfolio_data["wallets"][currency]["balance"] = old_balance - amount
        self._save_portfolio_for_user(user.user_id, portfolio_data)

        try:
            rate = self._get_exchange_rate(currency, "USD")
            revenue_usd = amount * rate
        except UserError:
            rate = None
            revenue_usd = None

        result = f"Продажа выполнена: {amount:.4f} {currency}"
        if rate is not None:
            result += f" по курсу {rate:,.2f} USD/{currency}"
            result += f"\nОценочная выручка: {revenue_usd:,.2f} USD"
        result += f"\nИзменения в портфеле:\n- {currency}: было {old_balance:.4f} -> стало {old_balance - amount:.4f}"
        return result

    def get_exchange_rate(self, from_curr: str, to_curr: str) -> str:
        """Получение курса обмена между двумя валютами"""
        from_curr = from_curr.upper().strip()
        to_curr = to_curr.upper().strip()
        if not from_curr or not to_curr:
            raise UserError("Коды валют не могут быть пустыми")

        try:
            rate = self._get_exchange_rate(from_curr, to_curr)
            reverse_rate = self._get_exchange_rate(to_curr, from_curr)
            rates = self._load_rates()
            updated_at = rates.get("last_refresh", "неизвестно")
            return f"Курс {from_curr}->{to_curr}: {rate:.6f} (обновлено: {updated_at})\nОбратный курс {to_curr}->{from_curr}: {reverse_rate:.2f}"
        except UserError:
            raise
        except Exception:
            raise UserError(f"Курс {from_curr}->{to_curr} недоступен. Повторите попытку позже.")