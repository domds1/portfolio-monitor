"""Test allocation threshold calculations and rebalance alert generation."""

import unittest

from portfolio_monitor.config import TARGET_CONFIG
from portfolio_monitor.models import TargetRule
from portfolio_monitor.rebalance_engine import calculate_threshold_bounds, evaluate_alerts


class RebalanceEngineTests(unittest.TestCase):
    def test_relative_threshold_bounds_are_calculated_correctly(self):
        min_weight, max_weight = calculate_threshold_bounds(
            target_weight=30.0,
            threshold=20.0,
            calc_mode="RELATIVE",
        )

        self.assertAlmostEqual(min_weight, 24.0)
        self.assertAlmostEqual(max_weight, 36.0)

    def test_absolute_threshold_bounds_are_calculated_correctly(self):
        min_weight, max_weight = calculate_threshold_bounds(
            target_weight=30.0,
            threshold=5.0,
            calc_mode="ABSOLUTE",
        )

        self.assertAlmostEqual(min_weight, 25.0)
        self.assertAlmostEqual(max_weight, 35.0)

    def test_alert_is_generated_for_weight_outside_allowed_range(self):
        target_config = {
            "TEST.MI": {
                "target_weight": 30.0,
                "type": "RELATIVE",
                "threshold": 20.0,
            }
        }

        portfolio_values = {"TEST.MI": 3900.0}
        total_portfolio_value = 10000.0
        prices = {"TEST.MI": 100.0}

        alerts = evaluate_alerts(
            target_config=target_config,
            portfolio_values=portfolio_values,
            total_portfolio_value=total_portfolio_value,
            prices=prices,
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].ticker, "TEST.MI")
        self.assertGreater(alerts[0].actual_weight, alerts[0].max_weight)

    def test_missing_target_position_is_treated_as_zero_weight(self):
        alerts = evaluate_alerts(
            target_config={
                "TEST.MI": {
                    "target_weight": 30.0,
                    "type": "ABSOLUTE",
                    "threshold": 5.0,
                }
            },
            portfolio_values={},
            total_portfolio_value=10000.0,
            prices={},
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].actual_weight, 0.0)
        self.assertEqual(alerts[0].direction, "🔻")

    def test_target_config_is_loaded_and_has_expected_keys(self):
        self.assertIn("VWCE.MI", TARGET_CONFIG)
        self.assertIn("VAGF.MI", TARGET_CONFIG)
        self.assertIn("GOLD.MI", TARGET_CONFIG)

    def test_target_rule_normalizes_calculation_mode(self):
        rule = TargetRule(
            ticker="TEST.MI",
            target_weight=30.0,
            calc_mode="relative",
            threshold=20.0,
        )

        self.assertEqual(rule.calc_mode, "RELATIVE")
        self.assertAlmostEqual(rule.min_weight, 24.0)

    def test_target_rule_rejects_invalid_calculation_mode(self):
        rule = TargetRule(
            ticker="TEST.MI",
            target_weight=30.0,
            calc_mode="unsupported",
            threshold=20.0,
        )

        with self.assertRaises(ValueError):
            _ = rule.min_weight


if __name__ == "__main__":
    unittest.main()
