"""Test validation rules for portfolio monitor configuration."""

import unittest

from portfolio_monitor.config import _merge_config, _validate_config


class ConfigTests(unittest.TestCase):
    def test_private_target_config_replaces_example_targets(self):
        merged = _merge_config(
            {
                "target_config": {"VWCE.MI": {"target_weight": 55}},
                "workaround_bundles": {"VWCE.MI": ["XDEM.MI"]},
            },
            {
                "target_config": {"EXUS.MI": {"target_weight": 30}},
                "workaround_bundles": {"XDPU.MI": ["XDEM.MI"]},
            },
        )

        self.assertEqual(set(merged["target_config"]), {"EXUS.MI"})
        self.assertEqual(set(merged["workaround_bundles"]), {"XDPU.MI"})

    def test_rejects_target_without_required_fields(self):
        with self.assertRaises(ValueError):
            _validate_config({"target_config": {"VWCE.MI": {}}})

    def test_rejects_invalid_threshold_type(self):
        with self.assertRaises(ValueError):
            _validate_config(
                {
                    "target_config": {
                        "VWCE.MI": {
                            "target_weight": 50,
                            "type": "INVALID",
                            "threshold": 5,
                        }
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()