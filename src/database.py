"""
Lokale database voor geplande uitzendingen (JSON-bestand)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class BroadcastDB:
    """Slaat lokaal geplande uitzendingen op"""

    def __init__(self, data_dir: Path):
        self.db_file = data_dir / "broadcasts.json"
        self.records = self._load()

    def _load(self) -> list:
        if self.db_file.exists():
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)

    def add(self, record: dict) -> dict:
        """Voeg een nieuwe uitzending toe"""
        record["created_at"] = datetime.now().isoformat()
        self.records.append(record)
        self._save()
        return record

    def get_all(self) -> list:
        return list(self.records)

    def get_upcoming(self) -> list:
        now = datetime.now().isoformat()
        return [r for r in self.records if r.get("scheduled_start", "") >= now]

    def get_past(self, limit: int = 50) -> list:
        now = datetime.now().isoformat()
        past = [r for r in self.records if r.get("scheduled_start", "") < now]
        return sorted(past, key=lambda x: x.get("scheduled_start", ""), reverse=True)[:limit]

    def find_by_broadcast_id(self, broadcast_id: str) -> Optional[dict]:
        for r in self.records:
            if r.get("main_broadcast_id") == broadcast_id or r.get("tolk_broadcast_id") == broadcast_id:
                return r
        return None

    def update(self, broadcast_id: str, updates: dict):
        for r in self.records:
            if r.get("main_broadcast_id") == broadcast_id:
                r.update(updates)
                self._save()
                return
