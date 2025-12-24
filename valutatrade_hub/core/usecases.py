import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any

from valutatrade_hub.core.models import User
from valutatrade_hub.core.currencies import get_currency, CurrencyNotFoundError
from valutatrade_hub.core.exceptions import UserError, InsufficientFundsError, ApiRequestError
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.decorators import log_action


# Глобальная сессия
_current_user: Optional[User] = None


class UseCases:
    """Основной класс для бизнес-логики приложения"""

    def __init__(self) -> None:
        self.db = DatabaseManager()
        settings = SettingsLoader()
        self.rates_ttl = settings.get("rates_ttl_seconds")
        self.default_base_currency = settings.get("default_base_currency")

    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя по имени"""
        users = self.db.load_users()
        for user in users:
            if user["username"] == username:
                return user
        return None

    def _get_portfolio_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение портфеля по ID пользователя"""
        portfolios = self.db.load_portfolios()
        for portfolio in portfolios:
            if portfolio["user_id"] == user_id:
                return portfolio
        return None

    def _save_portfolio_for_user(self, user_id: int, portfolio_dict: Dict[str, Any]) -> None:
        """Сохранение портфеля для пользователя"""
        portfolios = self.db.load_portfolios()
        for i, p in enumerate(portfolios):
            if p["user_id"] == user_id:
                portfolios[i] = portfolio_dict
                self.db.save_portfolios(portfolios)
                return
        portfolios.append(portfolio_dict)
        self.db.save_portfolios(portfolios)

    def _get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        """Расчёт курса из одной валюты в другую через USD"""
        get_currency(from_curr)
        get_currency(to_curr)

        rates = self.db.load_rates()
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        if from_curr == to_curr:
            return 1.0

        supported = ["USD", "EUR", "RUB", "BTC", "ETH", "SOL"]
        if from_curr not in supported or to_curr not in supported:
            raise CurrencyNotFoundError("Валюта не поддерживается")

        def get_usd_rate(code: str) -> float:
            if code == "USD":
                return 1.0
            pair = f"{code}_USD"
            if pair in rates:
                return rates[pair]["rate"]
            raise UserError(f"Нет курса для {code} к USD")

        from_usd = get_usd_rate(from_curr)
        to_usd = get_usd_rate(to_curr)
        
        return from_usd / to_usd

    def get_logged_in_user(self) -> User:
        """Получение текущего авторизованного пользователя"""
        if _current_user is None:
            raise UserError("Сначала выполните login")
        return _current_user

    @log_action("REGISTER")
    def register_user(self, username: str, password: str) -> str:
        """Регистрация нового пользователя"""
        if len(password) < 4:
            raise UserError("Пароль должен быть не короче 4 символов")

        if self._get_user_by_username(username):
            raise UserError(f"Имя пользователя '{username}' уже занято")

        users = self.db.load_users()
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
        self.db.save_users(users)

        self._save_portfolio_for_user(user_id, {"user_id": user_id, "wallets": {}})

        return f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"

    @log_action("LOGIN")
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
        """Показ портфолио пользователя"""
        get_currency(base)
        user = self.get_logged_in_user()
        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if not portfolio_data or not portfolio_data["wallets"]:
            return f"Портфель пользователя '{user.username}' пуст."

        base = base.upper()
        wallets = portfolio_data["wallets"]
        lines = []
        total_in_base = 0.0

        for code, wallet in wallets.items():
            balance = wallet["balance"]
            if code == base:
                converted = balance
            else:
                try:
                    rate = self._get_exchange_rate(code, base)
                    converted = balance * rate
                except (UserError, CurrencyNotFoundError):
                    converted = 0.0
            lines.append(f"- {code}: {balance:.4f} -> {converted:.2f} {base}")
            total_in_base += converted

        result = f"Портфель пользователя '{user.username}' (база: {base}):\n"
        result += "\n".join(lines)
        result += f"\n{'-' * 33}\nИТОГО: {total_in_base:,.2f} {base}"
        return result

    @log_action("BUY", verbose=True)
    def buy_currency(self, currency: str, amount: float) -> str:
        """Покупка валюты"""
        user = self.get_logged_in_user()
        if amount <= 0:
            raise UserError("'amount' должен быть положительным числом")
        get_currency(currency)

        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if currency not in portfolio_data["wallets"]:
            portfolio_data["wallets"][currency] = {"balance": 0.0}

        old_balance = portfolio_data["wallets"][currency]["balance"]
        portfolio_data["wallets"][currency]["balance"] = old_balance + amount
        self._save_portfolio_for_user(user.user_id, portfolio_data)

        try:
            rate = self._get_exchange_rate(currency, "USD")
            cost_usd = amount * rate
        except (UserError, CurrencyNotFoundError):
            rate = None
            cost_usd = None

        result = f"Покупка выполнена: {amount:.4f} {currency}"
        if rate is not None:
            result += f" по курсу {rate:,.2f} USD/{currency}"
            result += f"\nОценочная стоимость покупки: {cost_usd:,.2f} USD"
        result += f"\nИзменения в портфеле:\n- {currency}: было {old_balance:.4f} -> стало {old_balance + amount:.4f}"
        return result

    @log_action("SELL", verbose=True)
    def sell_currency(self, currency: str, amount: float) -> str:
        """Продажа валюты"""
        user = self.get_logged_in_user()
        if amount <= 0:
            raise UserError("'amount' должен быть положительным числом")
        get_currency(currency)

        portfolio_data = self._get_portfolio_by_user_id(user.user_id)
        if currency not in portfolio_data["wallets"]:
            raise UserError(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")

        balance = portfolio_data["wallets"][currency]["balance"]
        if amount > balance:
            raise InsufficientFundsError(available=balance, required=amount, code=currency)

        old_balance = balance
        portfolio_data["wallets"][currency]["balance"] = old_balance - amount
        self._save_portfolio_for_user(user.user_id, portfolio_data)

        try:
            rate = self._get_exchange_rate(currency, "USD")
            revenue_usd = amount * rate
        except (UserError, CurrencyNotFoundError):
            rate = None
            revenue_usd = None

        result = f"Продажа выполнена: {amount:.4f} {currency}"
        if rate is not None:
            result += f" по курсу {rate:,.2f} USD/{currency}"
            result += f"\nОценочная выручка: {revenue_usd:,.2f} USD"
        result += f"\nИзменения в портфеле:\n- {currency}: было {old_balance:.4f} -> стало {old_balance - amount:.4f}"
        return result

    @log_action("GET_RATE")
    def get_exchange_rate(self, from_curr: str, to_curr: str) -> str:
        """Получение курса с проверкой TTL"""
        from_curr = from_curr.upper().strip()
        to_curr = to_curr.upper().strip()
        if not from_curr or not to_curr:
            raise UserError("Коды валют не могут быть пустыми")

        get_currency(from_curr)
        get_currency(to_curr)

        # Проверка TTL
        if not self.db.is_rates_cache_fresh(self.rates_ttl):
            raise ApiRequestError("Курсы устарели и не могут быть обновлены")

        try:
            rate = self._get_exchange_rate(from_curr, to_curr)
            reverse_rate = self._get_exchange_rate(to_curr, from_curr)
            rates = self.db.load_rates()
            updated_at = rates.get("last_refresh", "неизвестно")
            return f"Курс {from_curr}->{to_curr}: {rate:.6f} (обновлено: {updated_at})\nОбратный курс {to_curr}->{from_curr}: {reverse_rate:.2f}"
        except (UserError, CurrencyNotFoundError):
            raise
        except Exception:
            raise UserError(f"Курс {from_curr}->{to_curr} недоступен. Повторите попытку позже.")
        
    def show_rates(self, currency: str = None, top_n: int = None) -> str:
        """Возвращает форматированную строку с курсами из кеша"""
        from valutatrade_hub.parser_service.config import ParserConfig
        
        try:
            data = self.db.load_rates()
        except Exception:
            raise UserError("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")

        last_refresh = data.get("last_refresh", "неизвестно")
        pairs = {k: v for k, v in data.items() if k != "last_refresh"}

        if not pairs:
            raise UserError("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")

        # Фильтрация по валюте
        if currency:
            cur = currency.upper()
            filtered = {}
            for pair in pairs:
                from_curr, to_curr = pair.split("_", 1)
                if from_curr == cur or to_curr == cur:
                    filtered[pair] = pairs[pair]
            if not filtered:
                raise UserError(f"Курс для '{cur}' не найден в кеше.")

        # Топ криптовалют
        elif top_n is not None:
            config = ParserConfig()
            crypto_set = set(config.CRYPTO_CURRENCIES)
            crypto_usd_pairs = {}
            for pair, info in pairs.items():
                if pair.endswith("_USD"):
                    crypto_code = pair[:-4]
                    if crypto_code in crypto_set:
                        crypto_usd_pairs[pair] = info
            sorted_items = sorted(crypto_usd_pairs.items(), key=lambda x: x[1]["rate"], reverse=True)
            filtered = dict(sorted_items[:top_n])

        # Без аргументов
        else:
            filtered = pairs

        lines = [f"Курсы валют из кеша, последнее обновление: {last_refresh}:"]
        for pair, info in filtered.items():
            lines.append(f"- {pair}: {info['rate']:.2f}")
        return "\n".join(lines)