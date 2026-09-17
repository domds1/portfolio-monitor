from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_prices_for_tickers(tickers: list[str]) -> dict[str, float]:
    """Download close prices for a list of tickers from Yahoo Finance."""
    if not tickers:
        return {}

    data = yf.download(tickers, period="2d", interval="1d", progress=False)
    prices: dict[str, float] = {}

    for ticker in tickers:
        try:
            close_data = data["Close"]
            if isinstance(close_data, pd.DataFrame):
                if ticker in close_data.columns:
                    close_series = close_data[ticker].dropna()
                else:
                    close_series = close_data.iloc[:, 0].dropna()
            else:
                close_series = close_data.dropna()

            if close_series.empty:
                continue
            prices[ticker] = float(close_series.iloc[-1])
        except Exception as exc:  # pragma: no cover - defensive logging path
            print(f"Error fetching market price for {ticker}: {exc}")

    return prices
