"""Test transaction CSV parsing and input validation."""

import tempfile
import unittest
from pathlib import Path

from portfolio_monitor.portfolio_loader import calculate_quantities_from_csv


class PortfolioLoaderTests(unittest.TestCase):
    def test_calculates_net_quantities_from_required_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "portfolio.csv"
            path.write_text(
                "Symbol,Quantity,Transaction Type,Extra\n"
                "VWCE.MI,10,BUY,ignored\n"
                "VWCE.MI,2,SELL,ignored\n",
                encoding="utf-8",
            )

            quantities = calculate_quantities_from_csv(str(path), {"VWCE.MI"})

        self.assertEqual(quantities, {"VWCE.MI": 8})

    def test_rejects_csv_without_required_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "portfolio.csv"
            path.write_text("Symbol,Quantity\nVWCE.MI,10\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                calculate_quantities_from_csv(str(path), {"VWCE.MI"})


if __name__ == "__main__":
    unittest.main()