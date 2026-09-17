"""Calculate allocation thresholds and produce portfolio rebalance alerts."""

from __future__ import annotations

from typing import Any

from .models import Alert, TargetRule


def calculate_threshold_bounds(
    target_weight: float,
    threshold: float,
    calc_mode: str,
) -> tuple[float, float]:
    """Calculate the minimum and maximum allowed allocation percentages."""
    calc_mode = calc_mode.upper()
    if calc_mode == "RELATIVE":
        delta = target_weight * (threshold / 100.0)
        return target_weight - delta, target_weight + delta
    if calc_mode == "ABSOLUTE":
        return target_weight - threshold, target_weight + threshold
    raise ValueError(f"Invalid calculation mode '{calc_mode}'")


def build_target_rules(target_config: dict[str, dict[str, Any]]) -> dict[str, TargetRule]:
    """Convert raw target configuration dictionaries into typed target rules."""
    return {
        ticker: TargetRule(
            ticker=ticker,
            target_weight=float(config["target_weight"]),
            calc_mode=str(config["type"]).upper(),
            threshold=float(config["threshold"]),
        )
        for ticker, config in target_config.items()
    }


def evaluate_alerts(
    target_config: dict[str, dict[str, Any]],
    portfolio_values: dict[str, float],
    total_portfolio_value: float,
    prices: dict[str, float],
) -> list[Alert]:
    """Create alerts for target allocations outside their configured ranges."""
    alerts: list[Alert] = []

    for ticker, config in target_config.items():
        actual_value = portfolio_values.get(ticker, 0.0)
        actual_weight = (actual_value / total_portfolio_value) * 100.0

        target_weight = float(config["target_weight"])
        calc_mode = str(config["type"]).upper()
        threshold = float(config["threshold"])

        min_weight, max_weight = calculate_threshold_bounds(
            target_weight=target_weight,
            threshold=threshold,
            calc_mode=calc_mode,
        )

        if actual_weight < min_weight or actual_weight > max_weight:
            mode_str = f"Relative {threshold}%" if calc_mode == "RELATIVE" else f"Absolute {threshold}%"
            alerts.append(
                Alert(
                    ticker=ticker,
                    actual_weight=actual_weight,
                    target_weight=target_weight,
                    min_weight=min_weight,
                    max_weight=max_weight,
                    mode_str=mode_str,
                    current_price=prices.get(ticker, 0.0),
                )
            )

    return alerts


def build_summary_lines(
    target_config: dict[str, dict[str, Any]],
    portfolio_values: dict[str, float],
    total_portfolio_value: float,
) -> list[str]:
    """Build formatted allocation summary lines for notification messages."""
    lines: list[str] = []
    for ticker, config in target_config.items():
        actual_value = portfolio_values.get(ticker, 0.0)
        actual_weight = (actual_value / total_portfolio_value) * 100.0 if total_portfolio_value else 0.0
        lines.append(
            f"- *{ticker}*: `{actual_weight:.2f}%` vs target `{float(config['target_weight']):.2f}%`"
        )
    return lines
