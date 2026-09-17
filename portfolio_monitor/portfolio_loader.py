"""Read transaction history and calculate net quantities per allowed ticker."""

from __future__ import annotations

import pandas as pd


def calculate_quantities_from_csv(
    file_path: str, allowed_tickers: set[str]
) -> dict[str, float]:
    """Read the portfolio CSV and compute net quantities only for allowed tickers."""
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    required_columns = {"Symbol", "Quantity", "Transaction Type"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Portfolio CSV is missing required columns: {missing}.")

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Transaction Type"] = (
        df["Transaction Type"].astype(str).str.strip().str.upper()
    )

    quantities = {ticker: 0.0 for ticker in allowed_tickers}

    for _, row in df.iterrows():
        symbol = str(row["Symbol"]).strip()
        if symbol not in allowed_tickers:
            continue

        qty = row["Quantity"]
        tx_type = row["Transaction Type"]

        if tx_type == "BUY":
            quantities[symbol] += qty
        elif tx_type == "SELL":
            quantities[symbol] -= qty

    return {ticker: value for ticker, value in quantities.items() if value > 0}
