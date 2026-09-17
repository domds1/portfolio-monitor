import json
import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
PRIVATE_CONFIG_PATH = BASE_DIR / "config.json"
EXAMPLE_CONFIG_PATH = BASE_DIR / "config.example.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, OSError):
        return {}


def _build_default_config() -> dict[str, Any]:
    return {
        "csv_path": "portfolio.csv",
        "telegram_bot_token": None,
        "telegram_chat_id": None,
        "enable_aggregation_workaround": True,
        "target_config": {
            "VWCE.MI": {"target_weight": 55.0, "type": "RELATIVE", "threshold": 20.0},
            "VAGF.MI": {"target_weight": 35.0, "type": "RELATIVE", "threshold": 20.0},
            "GOLD.MI": {"target_weight": 10.0, "type": "ABSOLUTE", "threshold": 5.0},
        },
        "workaround_bundles": {
            "VAGF.MI": ["EGOV.MI", "XBLC.MI"],
            "VWCE.MI": ["XDEM.MI", "MVOL.MI"],
        },
    }


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


PRIVATE_CONFIG = _load_json(PRIVATE_CONFIG_PATH)
EXAMPLE_CONFIG = _load_json(EXAMPLE_CONFIG_PATH)
CONFIG = _merge_config(_build_default_config(), EXAMPLE_CONFIG)
CONFIG = _merge_config(CONFIG, PRIVATE_CONFIG)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", CONFIG.get("telegram_bot_token"))
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", CONFIG.get("telegram_chat_id"))
CSV_PATH = os.getenv("CSV_PATH", CONFIG.get("csv_path", "portfolio.csv"))

TARGET_CONFIG: dict[str, dict[str, Any]] = CONFIG.get("target_config", {})

WORKAROUND_BUNDLES: dict[str, set[str]] = {
    ticker: set(tickers)
    for ticker, tickers in CONFIG.get("workaround_bundles", {}).items()
}

ENABLE_AGGREGATION_WORKAROUND = bool(
    CONFIG.get("enable_aggregation_workaround", True)
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", CONFIG.get("telegram_bot_token"))
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", CONFIG.get("telegram_chat_id"))
CSV_PATH = os.getenv("CSV_PATH", CONFIG.get("csv_path", "portfolio.csv"))

TARGET_CONFIG: dict[str, dict[str, Any]] = CONFIG.get("target_config", {})

WORKAROUND_BUNDLES: dict[str, set[str]] = {
    ticker: set(tickers)
    for ticker, tickers in CONFIG.get("workaround_bundles", {}).items()
}

ENABLE_AGGREGATION_WORKAROUND = bool(
    CONFIG.get("enable_aggregation_workaround", True)
)
