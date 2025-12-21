import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> None:
    """Настройка логирования"""
    settings = SettingsLoader()
    log_file = Path(settings.get("log_file", "logs/actions.log"))
    
    # Создание директории
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(getattr(logging, settings.get("log_level", "INFO")))

    # Очистка
    if logger.handlers:
        logger.handlers.clear()

    # Файловый обработчик
    handler = RotatingFileHandler(
        log_file,
        maxBytes=int(settings.get("log_max_bytes", 5242880)),
        backupCount=int(settings.get("log_backup_count", 3)),
        encoding="utf-8"
    )
    log_format = settings.get("log_format", "%(levelname)s %(asctime)s %(message)s")
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Вывод логов в консоль
   # console = logging.StreamHandler()
   # console.setFormatter(formatter)
   # logger.addHandler(console)