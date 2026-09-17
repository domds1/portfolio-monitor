"""Coordinate portfolio loading, valuation, rebalance checks, and notifications."""

from __future__ import annotations

from pathlib import Path

from .config import (
    BASE_DIR,
    CSV_PATH,
    ENABLE_AGGREGATION_WORKAROUND,
    EXAMPLE_CSV_PATH,
    TARGET_CONFIG,
    USING_EXAMPLE_CONFIG,
    WORKAROUND_BUNDLES,
)
from .market_data import fetch_prices_for_tickers
from .portfolio_loader import calculate_quantities_from_csv
from .rebalance_engine import build_summary_lines, evaluate_alerts
from .telegram_notifier import build_alert_message, send_telegram_message


def get_allowed_tickers() -> set[str]:
    """Return target tickers plus optional secondary aggregation tickers."""
    target_tickers = set(TARGET_CONFIG.keys())
    if not ENABLE_AGGREGATION_WORKAROUND:
        return target_tickers

    extra_tickers = {
        ticker
        for bundle in WORKAROUND_BUNDLES.values()
        for ticker in bundle
    }
    return target_tickers.union(extra_tickers)


def apply_workaround_aggregation(
    portfolio_values: dict[str, float],
) -> dict[str, float]:
    """Fold configured secondary position values into their target tickers."""
    if not ENABLE_AGGREGATION_WORKAROUND:
        return portfolio_values

    aggregated = dict(portfolio_values)
    for target_ticker, bundle_tickers in WORKAROUND_BUNDLES.items():
        bundled_value = sum(aggregated.get(ticker, 0.0) for ticker in bundle_tickers)
        if target_ticker in aggregated:
            aggregated[target_ticker] += bundled_value
        else:
            aggregated[target_ticker] = bundled_value
    return aggregated


def monitor_portfolio() -> None:
    """Run one portfolio valuation, threshold evaluation, and notification cycle."""
    allowed_tickers = get_allowed_tickers()
    csv_path = CSV_PATH
    if USING_EXAMPLE_CONFIG:
        print(
            "WARNING: using example configuration (config.example.json).\n"
            "Create config.json with your personal settings before relying "
            "on monitoring results."
        )

    if USING_EXAMPLE_CONFIG and not Path(csv_path).exists():
        csv_path = str(EXAMPLE_CSV_PATH.relative_to(BASE_DIR))
        print(
            "WARNING: private portfolio CSV not found.\n"
            f"Using sample data from '{csv_path}'. Create portfolio.csv "
            "with your personal transactions."
        )

    try:
        quantities = calculate_quantities_from_csv(csv_path, allowed_tickers)
    except (OSError, ValueError) as exc:
        print(f"Unable to read portfolio CSV '{csv_path}': {exc}")
        return

    if not quantities:
        print("No active tickers matching the configuration were found in the CSV.")
        return

    active_tickers = list(quantities.keys())
    prices = fetch_prices_for_tickers(active_tickers)
    missing_prices = sorted(set(active_tickers) - set(prices))
    if missing_prices:
        print(f"Unable to value portfolio; missing prices for: {', '.join(missing_prices)}")
        return

    portfolio_values: dict[str, float] = {}
    total_portfolio_value = 0.0
    for symbol, qty in quantities.items():
        value = qty * prices[symbol]
        portfolio_values[symbol] = value
        total_portfolio_value += value

    if total_portfolio_value == 0:
        print("Total portfolio value is zero.")
        return

    portfolio_values = apply_workaround_aggregation(portfolio_values)
    alerts = evaluate_alerts(
        target_config=TARGET_CONFIG,
        portfolio_values=portfolio_values,
        total_portfolio_value=total_portfolio_value,
        prices=prices,
    )

    summary_lines = build_summary_lines(
        target_config=TARGET_CONFIG,
        portfolio_values=portfolio_values,
        total_portfolio_value=total_portfolio_value,
    )

    if alerts:
        message = build_alert_message(alerts, summary_lines)
        try:
            send_telegram_message(message)
        except (RuntimeError, ValueError) as exc:
            print(f"Telegram alert was not sent: {exc}")
            return
        print("Telegram alert sent successfully.")
    else:
        print("All monitored assets are within allowed threshold ranges.")
