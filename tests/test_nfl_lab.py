"""CI checks for the nfl-lab site section (arena/909635f5-own4).
Run: python -m unittest discover -s tests -v  (picked up by .github/workflows/pages.yml)
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class NflLabSite(unittest.TestCase):
    def test_audit_site(self):
        """Every table row carries an allow-listed https source link; no broken links;
        market cells blank; flagged page populated."""
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "nfl-lab", "scripts", "audit_site.py")],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)

    def test_verification_report_all_pass(self):
        """The line-by-line data verification must pass (14 checks, 0 failures)."""
        import json
        p = os.path.join(ROOT, "nfl-lab", "data", "verification_report.json")
        with open(p) as f:
            rep = json.load(f)
        self.assertTrue(rep["all_pass"], msg=str([c for c in rep["checks"] if not c["pass"]]))
        self.assertEqual(rep["games"], 120)
        self.assertEqual(rep["standings_rows"], 32)

    def test_own_lines_exist_and_flagged(self):
        """Own lines published for the upcoming slate; market columns blank."""
        import csv
        p = os.path.join(ROOT, "nfl-lab", "data", "own_lines_2026.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 16)
        for r in rows:
            self.assertNotEqual(r["p_home"], "")
            self.assertEqual(r["market_ml"], "")
            self.assertEqual(r["market_spread"], "")
            self.assertEqual(r["market_total"], "")
            self.assertTrue(r["source_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
