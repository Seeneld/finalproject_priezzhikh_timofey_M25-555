import os
from dataclasses import dataclass, field
from typing import Tuple, Dict


def _default_crypto_id_map() -> Dict[str, str]:
    return {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

def _default_fiat_currencies() -> Tuple[str, ...]:
    return ("EUR", "GBP", "RUB")

def _default_crypto_currencies() -> Tuple[str, ...]:
    return ("BTC", "ETH", "SOL")


@dataclass
class ParserConfig:
    # Ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    # Эндпоинты
    COINGECKO_URL: str = " https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = field(default_factory=_default_fiat_currencies)
    CRYPTO_CURRENCIES: Tuple[str, ...] = field(default_factory=_default_crypto_currencies)
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=_default_crypto_id_map)

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10