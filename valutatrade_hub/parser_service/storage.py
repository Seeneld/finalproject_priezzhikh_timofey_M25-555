import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    def __init__(self, config: ParserConfig):
        self.config = config
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        Path(self.config.RATES_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, pairs: Dict[str, Dict[str, Any]]) -> int:
        """Сохранение курсов в совместимом формате"""
        data = {}
        for pair, info in pairs.items():
            data[pair] = {
                "rate": info["rate"],
                "updated_at": info["updated_at"]
            }
        data["last_refresh"] = max(
            (info["updated_at"] for info in pairs.values()),
            default=datetime.now().isoformat()
        )

        with tempfile.NamedTemporaryFile("w", delete=False, dir=Path(self.config.RATES_FILE_PATH).parent) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            os.replace(tmp.name, self.config.RATES_FILE_PATH)
        return len(pairs)

    def append_to_history(self, pair: str, rate: float, source: str) -> None:
        from_curr, to_curr = pair.split("_")
        timestamp = datetime.now().isoformat()
        record_id = f"{from_curr}_{to_curr}_{timestamp}"

        record = {
            "id": record_id,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "rate": rate,
            "timestamp": timestamp,
            "source": source
        }

        history_path = Path(self.config.HISTORY_FILE_PATH)
        history = []
        if history_path.exists():
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.append(record)

        with tempfile.NamedTemporaryFile("w", delete=False, dir=history_path.parent) as tmp:
            json.dump(history, tmp, indent=2, ensure_ascii=False)
            os.replace(tmp.name, history_path)