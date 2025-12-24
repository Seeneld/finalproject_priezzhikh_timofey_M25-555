import threading
from typing import Optional

from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.config import ParserConfig
import logging

logger = logging.getLogger("valutatrade")


class RatesScheduler:
    """Планировщик периодического обновления курсов валют в фоновом режиме."""

    def __init__(self, interval_seconds: int = 120):  # по умолчанию каждые две минуты
        self.interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.config = ParserConfig()
        self.updater = RatesUpdater(self.config)

    def _run(self) -> None:
        """Основной цикл обновления"""
        logger.info(f"Планировщик запущен. Интервал: {self.interval} секунд")
        while not self._stop_event.wait(self.interval):
            try:
                logger.info("Планировщик: запуск обновления курсов...")
                count = self.updater.run_update()
                logger.info(f"Планировщик: обновлено {count} курсов")
            except Exception as e:
                logger.error(f"Планировщик: ошибка при обновлении — {e}")

    def start(self) -> None:
        """Запуск фонового потока с первым обновлением"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Планировщик уже запущен")
            return
        
        self._stop_event.clear()
        
        try:
            logger.info("Планировщик: первое обновление курсов при старте...")
            count = self.updater.run_update()
            logger.info(f"Планировщик: первое обновление завершено. Получено {count} курсов")
        except Exception as e:
            logger.error(f"Планировщик: ошибка при первом обновлении — {e}")
        
        # Запуск фонового потока для периодических обновлений
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Планировщик активирован")

    def stop(self) -> None:
        """Остановка фонового потока"""
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join(timeout=2.0)
            logger.info("Планировщик остановлен")

    def is_running(self) -> bool:
        """Проверка, запущен ли планировщик"""
        return self._thread is not None and self._thread.is_alive()