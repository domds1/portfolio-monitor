"""Load portfolio settings from built-in defaults, local JSON, and the environment."""

import json
import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
PRIVATE_CONFIG_PATH = BASE_DIR / "config.json"
EXAMPLE_CONFIG_PATH = BASE_DIR / "config.example.json"
EXAMPLE_CSV_PATH = BASE_DIR / "portfolio-template.csv"


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk, returning an empty mapping when absent."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Unable to load configuration file '{path}'.") from exc

    if not isinstance(loaded, dict):
        raise ValueError(f"Configuration file '{path}' must contain a JSON object.")
    return loaded


def _build_default_config() -> dict[str, Any]:
    """Return the built-in configuration used when no template is available."""
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
    """Recursively merge override values into a configuration mapping."""
    merged = base.copy()
    for key, value in override.items():
        if key in {"target_config", "workaround_bundles"}:
            merged[key] = value
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_config(config: dict[str, Any]) -> None:
    """Validate the fields required to run the portfolio monitor."""
    target_config = config.get("target_config")
    if not isinstance(target_config, dict) or not target_config:
        raise ValueError("Configuration must define at least one target ticker.")

    for ticker, rule in target_config.items():
        if not isinstance(rule, dict):
            raise ValueError(f"Target configuration for '{ticker}' must be an object.")
        missing_keys = {"target_weight", "type", "threshold"} - rule.keys()
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"Target '{ticker}' is missing configuration keys: {missing}.")
        try:
            target_weight = float(rule["target_weight"])
            threshold = float(rule["threshold"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Target '{ticker}' has non-numeric weights or threshold.") from exc
        if target_weight < 0 or threshold < 0:
            raise ValueError(f"Target '{ticker}' cannot have negative weights or threshold.")
        if str(rule["type"]).upper() not in {"RELATIVE", "ABSOLUTE"}:
            raise ValueError(f"Target '{ticker}' has an invalid threshold type.")

    bundles = config.get("workaround_bundles", {})
    if not isinstance(bundles, dict) or any(
        not isinstance(tickers, list) for tickers in bundles.values()
    ):
        raise ValueError("workaround_bundles must map tickers to lists of tickers.")


PRIVATE_CONFIG = _load_json(PRIVATE_CONFIG_PATH)
EXAMPLE_CONFIG = _load_json(EXAMPLE_CONFIG_PATH)
CONFIG = _merge_config(_build_default_config(), EXAMPLE_CONFIG)
CONFIG = _merge_config(CONFIG, PRIVATE_CONFIG)
_validate_config(CONFIG)

USING_EXAMPLE_CONFIG = not PRIVATE_CONFIG_PATH.exists()

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
