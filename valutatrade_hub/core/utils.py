import json
from pathlib import Path
from typing import Any


def file_exists(path: str) -> bool:
    """Проверка существования файла по пути"""
    return Path(path).exists()


def ensure_file_exists(path: str, default_content: str) -> None:
    """Создание файла с содержимым по умолчанию, если он не существует"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    if not path_obj.exists():
        with open(path_obj, "w", encoding="utf-8") as f:
            f.write(default_content)


def load_json_file(path: str) -> Any:
    """Загрузка данных из JSON-файла"""
    if not file_exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: str, data: Any) -> None:
    """Сохранение данных в JSON-файл"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)