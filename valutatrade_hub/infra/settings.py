import json
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsLoader:
    """Синглтон для загрузки конфигурации из config.json."""
    _instance: Optional['SettingsLoader'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SettingsLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Перезагрузка конфигурации из config.json"""
        config_path = Path("config.json")
        if not config_path.exists():
            raise FileNotFoundError(
                "Файл конфигурации не найден: config.json. "
                "Создайте его в корне проекта."
            )
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения параметра конфигурации по ключу"""
        return self._config.get(key, default)