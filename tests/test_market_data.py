import unittest
from unittest.mock import patch

import pandas as pd

from portfolio_monitor.market_data import fetch_prices_for_tickers


class MarketDataTests(unittest.TestCase):
    def test_missing_ticker_is_not_assigned_another_tickers_price(self):
        close_data = pd.DataFrame({"KNOWN.MI": [100.0, 101.0]})
        downloaded_data = pd.concat({"Close": close_data}, axis=1)

        with patch(
            "portfolio_monitor.market_data.yf.download",
            return_value=downloaded_data,
        ):
            prices = fetch_prices_for_tickers(["MISSING.MI"])

        self.assertEqual(prices, {})


if __name__ == "__main__":
    unittest.main()