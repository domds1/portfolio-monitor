import requests

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(message: str) -> None:
    """Send a formatted Markdown text message to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("Error sending Telegram message") from exc


def build_alert_message(alerts: list, summary_lines: list[str]) -> str:
    """Build a compact, professional Telegram alert message."""
    if not alerts:
        return ""

    alert_lines = []
    for alert in alerts:
        alert_lines.append(
            f"{alert.direction} *{alert.ticker}*\n"
            f"Current Weight: `{alert.actual_weight:.2f}%` (Target: `{alert.target_weight:.2f}%`)\n"
            f"Threshold Config: `{alert.mode_str}`\n"
            f"Allowed Range: `[{alert.min_weight:.2f}% - {alert.max_weight:.2f}%]`\n"
            f"Current Price: `{alert.current_price:.2f} EUR`"
        )

    summary_block = "\n\n*Target Allocation Summary*\n" + "\n".join(summary_lines)
    return "*PORTFOLIO ALERT*\n\n" + "\n\n".join(alert_lines) + summary_block
