#!/usr/bin/env python3
"""Unit and integration test suite for sf-rent-94122 compliance dashboard."""

from __future__ import annotations

import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import build_site  # noqa: E402
import verify_site  # noqa: E402


class TestSfRent94122(unittest.TestCase):
    def test_deterministic_rebuild_and_zero_verification_errors(self) -> None:
        build_site.main()
        errors = verify_site.verify_all()
        self.assertEqual(errors, [], f"Verification errors found: {errors}")

    def test_unit_calculations_no_rounding_up(self) -> None:
        units_data = json.loads((THIS_DIR / "data" / "units_and_rates.json").read_text(encoding="utf-8"))
        u1, u2 = units_data["units"][0], units_data["units"][1]
        self.assertEqual(Decimal("3995.00") * Decimal("0.016"), Decimal("63.92000"))
        self.assertTrue(u1["annual_1_6_pct_increase"].startswith("$63.92"))
        self.assertTrue(u1["annual_1_6_pct_new_rent"].startswith("$4,058.92"))
        self.assertEqual(Decimal("3150.00") * Decimal("0.016"), Decimal("50.40000"))
        self.assertTrue(u2["annual_1_6_pct_increase"].startswith("$50.40"))
        self.assertTrue(u2["annual_1_6_pct_new_rent"].startswith("$3,200.40"))

    def test_unverified_values_are_strictly_blank(self) -> None:
        units_data = json.loads((THIS_DIR / "data" / "units_and_rates.json").read_text(encoding="utf-8"))
        laws_data = json.loads((THIS_DIR / "data" / "laws_and_practices.json").read_text(encoding="utf-8"))

        self.assertEqual(units_data["current_allowable_rate"]["next_period_2027_2028_rate"], "")
        self.assertEqual(units_data["units"][0]["verified_banked_amount"], "")
        self.assertEqual(units_data["units"][1]["verified_banked_amount"], "")
        self.assertEqual(units_data["form_571_schedule"][0]["rate"], "")

        for flag in laws_data["flagged_items"]:
            self.assertEqual(flag["unverified_value"], "")

    def test_anonymized_placeholders_present(self) -> None:
        html_index = (THIS_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn("Tenant A1", html_index)
        self.assertIn("Tenant A4", html_index)
        self.assertIn("Tenant B1", html_index)
        self.assertIn("Tenant B2", html_index)


if __name__ == "__main__":
    unittest.main()
