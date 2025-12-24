import logging
from typing import List
from datetime import datetime, timezone

from valutatrade_hub.parser_service.api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.core.exceptions import ApiRequestError


logger = logging.getLogger("valutatrade")


class RatesUpdater:
    def __init__(self, config: ParserConfig):
        self.config = config
        self.storage = RatesStorage(config)
        self.clients: List[BaseApiClient] = [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config)
        ]

    def run_update(self, source: str = None) -> int:
        logger.info("Начало обновления курсов валют...")
        all_rates = {}
        timestamp = datetime.now().isoformat()
        errors = []

        clients_to_use = []
        if source is None:
            clients_to_use = self.clients
        elif source == "coingecko":
            clients_to_use = [c for c in self.clients if isinstance(c, CoinGeckoClient)]
        elif source == "exchangerate":
            clients_to_use = [c for c in self.clients if isinstance(c, ExchangeRateApiClient)]

        if not clients_to_use:
            raise ApiRequestError("Неизвестный источник. Используйте: coingecko или exchangerate")

        for client in clients_to_use:
            source_name = "CoinGecko" if isinstance(client, CoinGeckoClient) else "ExchangeRate-API"
            try:
                rates = client.fetch_rates()
                for pair, rate in rates.items():
                    all_rates[pair] = {
                        "rate": rate,
                        "updated_at": timestamp,
                        "source": source_name
                    }
                    self.storage.append_to_history(pair, rate, source_name)
                logger.info(f"{source_name}: OK ({len(rates)} курса)")
            except ApiRequestError as e:
                logger.error(f"Не удалось получить курс {source_name}: {e}")
                errors.append(str(e))

        if all_rates:
            self.storage.save_snapshot(all_rates)
            return len(all_rates)
        else:
            raise ApiRequestError("Не удалось получить ни одного курса")