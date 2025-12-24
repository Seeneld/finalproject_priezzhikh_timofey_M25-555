import requests
from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.core.exceptions import ApiRequestError


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        pass


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES)
        vs_currencies = self.config.BASE_CURRENCY.lower()
        url = f"{self.config.COINGECKO_URL}?ids={ids}&vs_currencies={vs_currencies}"

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"Ошибка сети при запросе к CoinGecko: {e}")

        rates = {}
        for code in self.config.CRYPTO_CURRENCIES:
            coin_id = self.config.CRYPTO_ID_MAP[code]
            if coin_id in data and self.config.BASE_CURRENCY.lower() in data[coin_id]:
                rate = data[coin_id][self.config.BASE_CURRENCY.lower()]
                rates[f"{code}_{self.config.BASE_CURRENCY}"] = float(rate)
        return rates


class ExchangeRateApiClient(BaseApiClient):
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("API-ключ для ExchangeRate-API не задан (EXCHANGERATE_API_KEY)")

    def fetch_rates(self) -> Dict[str, float]:
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get("result") != "success":
                raise ApiRequestError(f"ExchangeRate-API ошибка: {data.get('error-type', 'неизвестно')}")
        except requests.RequestException as e:
            raise ApiRequestError(f"Ошибка сети: {e}")


        rates = {}
        for code in self.config.FIAT_CURRENCIES:
            if code in data.get("conversion_rates", {}):
                inverse_rate = 1.0 / data["conversion_rates"][code]
                rates[f"{code}_{self.config.BASE_CURRENCY}"] = round(inverse_rate, 6)
        return rates