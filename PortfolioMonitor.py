import pandas as pd
import requests
import yfinance as yf
import os


# ==========================================
# 1. TELEGRAM AND FILE CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CSV_PATH = "portfolio.csv"

# ==========================================
# 2. TARGET ASSETS AND THRESHOLDS CONFIG
# ==========================================
# ONLY tickers defined in this dictionary will be loaded and monitored.
TARGET_CONFIG = {
    "VWCE.MI": {
        "target_weight": 55.0,  # Target weight in portfolio (%)
        "type": "RELATIVE",
        "threshold": 20.0,
    },
    "VAGF.MI": {
        "target_weight": 35.0,  # Target weight in portfolio (%)
        "type": "RELATIVE",
        "threshold": 20.0,
    },
    "GOLD.MI": {
        "target_weight": 10.0,  # Target weight in portfolio (%)
        "type": "ABSOLUTE",
        "threshold": 0.0,
    },
}

# =========================================================================
# [WORKAROUND BLOCK 1/3] TEMPORARY AGGREGATION CONFIGURATION
# TO DISABLE: Set ENABLE_AGGREGATION_WORKAROUND = False
# TO PERMANENTLY REMOVE: Delete this entire block
# =========================================================================
ENABLE_AGGREGATION_WORKAROUND = True

WORKAROUND_BUNDLES = {
    "VAGF.MI": {"EGOV.MI", "XBLC.MI"},
    "VWCE.MI": {"XDEM.MI", "MVOL.MI"},
}
# =========================================================================


def send_telegram_message(message: str) -> None:
    """Sends a formatted Markdown text message to the configured Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")


def calculate_quantities_from_csv(
    file_path: str, allowed_tickers: set[str]
) -> dict[str, float]:
    """Reads the portfolio CSV and computes net quantities ONLY for allowed tickers."""
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

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

        return {k: v for k, v in quantities.items() if v > 0}
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}


def monitor_portfolio() -> None:
    target_tickers = set(TARGET_CONFIG.keys())

    # =========================================================================
    # [WORKAROUND BLOCK 2/3] TICKER LIST EXTENSION
    # TO PERMANENTLY REMOVE: Replace this block with: allowed_tickers = target_tickers
    # =========================================================================
    if ENABLE_AGGREGATION_WORKAROUND:
        extra_tickers = {
            ticker
            for bundle in WORKAROUND_BUNDLES.values()
            for ticker in bundle
        }
        allowed_tickers = target_tickers.union(extra_tickers)
    else:
        allowed_tickers = target_tickers
    # =========================================================================

    # 1. Load CSV and compute net quantities
    quantities = calculate_quantities_from_csv(CSV_PATH, allowed_tickers)
    if not quantities:
        print("No active tickers matching the configuration were found in the CSV.")
        return

    active_tickers = list(quantities.keys())

    # 2. Download market prices from Yahoo Finance
    data = yf.download(active_tickers, period="2d", interval="1d", progress=False)

    prices = {}
    for ticker in active_tickers:
        try:
            if len(active_tickers) == 1:
                close_series = data["Close"].dropna()
            else:
                close_series = data["Close"][ticker].dropna()
            prices[ticker] = float(close_series.iloc[-1])
        except Exception as e:
            print(f"Error fetching market price for {ticker}: {e}")

    # 3. Calculate individual asset values and total portfolio value
    portfolio_values = {}
    total_portfolio_value = 0.0

    for symbol, qty in quantities.items():
        if symbol in prices:
            val = qty * prices[symbol]
            portfolio_values[symbol] = val
            total_portfolio_value += val

    if total_portfolio_value == 0:
        print("Total portfolio value is zero.")
        return

    # =========================================================================
    # [WORKAROUND BLOCK 3/3] EURO VALUE AGGREGATION
    # TO PERMANENTLY REMOVE: Delete this entire block
    # =========================================================================
    if ENABLE_AGGREGATION_WORKAROUND:
        for target_ticker, bundle_tickers in WORKAROUND_BUNDLES.items():
            bundled_value = sum(
                portfolio_values.get(t, 0.0) for t in bundle_tickers
            )
            if target_ticker in portfolio_values:
                portfolio_values[target_ticker] += bundled_value
            else:
                portfolio_values[target_ticker] = bundled_value
    # =========================================================================

    alerts = []

    # 4. Evaluate weight deviations against defined thresholds
    for ticker, config in TARGET_CONFIG.items():
        if ticker not in portfolio_values:
            continue

        actual_val = portfolio_values[ticker]
        actual_weight = (actual_val / total_portfolio_value) * 100.0

        target_w = config["target_weight"]
        calc_mode = config["type"].upper()
        thresh = config["threshold"]

        if calc_mode == "RELATIVE":
            delta = target_w * (thresh / 100.0)
            min_weight = target_w - delta
            max_weight = target_w + delta
            mode_str = f"Relative {thresh}%"
        elif calc_mode == "ABSOLUTE":
            min_weight = target_w - thresh
            max_weight = target_w + thresh
            mode_str = f"Absolute {thresh}%"
        else:
            print(f"Invalid calculation mode '{calc_mode}' for {ticker}.")
            continue

        if actual_weight < min_weight or actual_weight > max_weight:
            direction = "🔺" if actual_weight > max_weight else "🔻"
            alert_msg = (
                f"{direction} *{ticker}*\n"
                f"Current Weight: `{actual_weight:.2f}%` (Target: `{target_w:.2f}%`)\n"
                f"Threshold Config: `{mode_str}`\n"
                f"Allowed Range: `[{min_weight:.2f}% - {max_weight:.2f}%]`\n"
                f"Current Price: `{prices.get(ticker, 0.0):.2f} EUR`"
            )
            alerts.append(alert_msg)

    # 5. Build summary of all target assets and dispatch Telegram Notification
    summary_lines = []
    for ticker, config in TARGET_CONFIG.items():
        actual_val = portfolio_values.get(ticker, 0.0)
        actual_weight = (actual_val / total_portfolio_value) * 100.0
        summary_lines.append(
            f"- *{ticker}*: `{actual_weight:.2f}%` vs target `{config['target_weight']:.2f}%`"
        )

    summary_block = "\n\n*Target Allocation Summary*\n" + "\n".join(summary_lines)

    if alerts:
        header = "*PORTFOLIO ALERT*\n"
        full_message = header + "\n".join(alerts) + summary_block
        send_telegram_message(full_message)
        print("Telegram alert sent successfully.")
    else:
        print("All monitored assets are within allowed threshold ranges.")


if __name__ == "__main__":
    monitor_portfolio()
