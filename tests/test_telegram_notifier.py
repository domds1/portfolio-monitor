"""Test Telegram delivery failures and alert message formatting."""

import unittest
from unittest.mock import patch

import requests

from portfolio_monitor.models import Alert
from portfolio_monitor.telegram_notifier import build_alert_message, send_telegram_message


class TelegramNotifierTests(unittest.TestCase):
    def test_send_failure_is_propagated(self):
        with patch(
            "portfolio_monitor.telegram_notifier.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            with patch(
                "portfolio_monitor.telegram_notifier.TELEGRAM_BOT_TOKEN",
                "token",
            ), patch(
                "portfolio_monitor.telegram_notifier.TELEGRAM_CHAT_ID",
                "chat",
            ):
                with self.assertRaises(RuntimeError):
                    send_telegram_message("message")

    def test_alert_message_uses_underweight_direction(self):
        alert = Alert(
            ticker="TEST.MI",
            actual_weight=10.0,
            target_weight=30.0,
            min_weight=25.0,
            max_weight=35.0,
            mode_str="Absolute 5.0%",
            current_price=100.0,
        )

        message = build_alert_message([alert], [])

        self.assertIn("🔻 *TEST.MI*", message)


if __name__ == "__main__":
    unittest.main()