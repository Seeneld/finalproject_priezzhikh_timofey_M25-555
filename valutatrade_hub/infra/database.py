from typing import Any, Dict, List
from pathlib import Path
from datetime import datetime

from valutatrade_hub.core import utils
from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Управление локальной БД"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        settings = SettingsLoader()
        self.users_file = Path(settings.get("users_file"))
        self.portfolios_file = Path(settings.get("portfolios_file"))
        self.rates_file = Path(settings.get("rates_file"))
        self._ensure_data_files()

    def _ensure_data_files(self) -> None:
        """Создание файлов данных, если они отсутствуют"""
        utils.ensure_file_exists(str(self.users_file), "[]")
        utils.ensure_file_exists(str(self.portfolios_file), "[]")
        initial_rates = {
            "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
            "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
            "RUB_USD": {"rate": 0.01016, "updated_at": datetime.now().isoformat()},
            "ETH_USD": {"rate": 3720.00, "updated_at": datetime.now().isoformat()},
            "source": "ParserService",
            "last_refresh": datetime.now().isoformat()
        }
        if not self.rates_file.exists():
            utils.save_json_file(str(self.rates_file), initial_rates)

    def load_users(self) -> List[Dict[str, Any]]:
        """Загрузка списка пользователей из файла"""
        return utils.load_json_file(str(self.users_file))

    def save_users(self, users: List[Dict[str, Any]]) -> None:
        """Сохранение списка пользователей в файл"""
        utils.save_json_file(str(self.users_file), users)

    def load_portfolios(self) -> List[Dict[str, Any]]:
        """Загрузка списка портфелей из файла"""
        return utils.load_json_file(str(self.portfolios_file))

    def save_portfolios(self, portfolios: List[Dict[str, Any]]) -> None:
        """Сохранение списка портфелей в файл"""
        utils.save_json_file(str(self.portfolios_file), portfolios)

    def load_rates(self) -> Dict[str, Any]:
        """Загрузка текущих курсов валют из файла"""
        return utils.load_json_file(str(self.rates_file))

    def save_rates(self, rates: Dict[str, Any]) -> None:
        """Сохранение курсов валют в файл"""
        utils.save_json_file(str(self.rates_file), rates)

    def is_rates_cache_fresh(self, ttl_seconds: int) -> bool:
        """Проверка, не устарел ли кеш курсов"""
        rates = self.load_rates()
        last_refresh_str = rates.get("last_refresh")
        if not last_refresh_str:
            return False
        try:
            last_refresh = datetime.fromisoformat(last_refresh_str)
        except ValueError:
            return False
        now = datetime.now()
        return (now - last_refresh).total_seconds() < ttl_seconds