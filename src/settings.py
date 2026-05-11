"""
Instellingen beheer - laadt en slaat alle configuratie op in settings.json
"""

import json
import os
from pathlib import Path

APP_VERSION = "1.1.0"

DEFAULT_SETTINGS = {
    "app": {
        "theme": "dark",
        "language": "nl",
        "timezone": "Europe/Amsterdam",
        "archive_after_days": 180,
    },
    "accounts": {
        "main": {
            "name": "Hoofdstream",
            "credentials_file": "credentials_main.json",
            "token_file": "token_main.json",
            "channel_id": "",
            "enabled": True,
        },
        "tolk": {
            "name": "Tolkstream",
            "credentials_file": "credentials_tolk.json",
            "token_file": "token_tolk.json",
            "channel_id": "",
            "enabled": True,
        },
    },
    "predikanten": [
        {"naam": "ds. D.J. Diepenbroek", "afkorting": "DJD"},
        {"naam": "ds. P.C. Hoek", "afkorting": "PCH"},
    ],
    "titel_template": "{predikant} | {schriftgedeelte}",
    "standaard_omschrijving": "",
    "stream_defaults": {
        "privacy": "public",
        "category_id": "29",  # Nonprofits & Activism
        "made_for_kids": False,
        "enable_dvr": True,
        "enable_content_encryption": False,
        "record_from_start": True,
        "start_with_slate": False,
        "latency_preference": "normal",  # normal, low, ultraLow
    },
}


class SettingsManager:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Sla data op naast het exe-bestand
            if getattr(sys, "frozen", False):
                data_dir = os.path.dirname(sys.executable)
            else:
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data_dir / "settings.json"
        self.settings = self._load()

    def _load(self) -> dict:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Merge met defaults zodat nieuwe keys altijd aanwezig zijn
                return self._deep_merge(DEFAULT_SETTINGS, loaded)
            except Exception:
                return dict(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def get(self, *keys, default=None):
        val = self.settings
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val

    def set(self, *keys_and_value):
        *keys, value = keys_and_value
        d = self.settings
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        self.save()

    def get_predikanten(self) -> list:
        return self.settings.get("predikanten", [])

    def add_predikant(self, naam: str, afkorting: str = ""):
        predikanten = self.get_predikanten()
        predikanten.append({"naam": naam, "afkorting": afkorting})
        self.settings["predikanten"] = predikanten
        self.save()

    def remove_predikant(self, naam: str):
        predikanten = [p for p in self.get_predikanten() if p["naam"] != naam]
        self.settings["predikanten"] = predikanten
        self.save()

    def get_data_dir(self) -> Path:
        return self.data_dir


import sys
