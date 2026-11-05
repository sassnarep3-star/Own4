"""Structural regression tests for the bounded audit; no external truth claims."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit_build', HERE/'build.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class AuditTests(unittest.TestCase):
    def test_reproducible_outputs(self):
        files = ('index.html','coverage.html','flagged.html','report.json')
        before = {p: (HERE/p).read_bytes() for p in files}
        b.build()
        self.assertEqual(before, {p: (HERE/p).read_bytes() for p in files})

    def test_nba_source_link_coverage_is_structural(self):
        r = json.loads((HERE/'report.json').read_text())
        self.assertGreater(r['nba_pages'],0)
        self.assertEqual(r['nba_table_rows'],r['nba_rows_with_https_link'])
        self.assertIn('NOT verified',r['limits'])
        self.assertTrue(all(row['file'].startswith('nfl/') for row in r['missing_external_source_rows']))

    def test_audit_rows_and_local_navigation(self):
        stats, missing, broken = b.scan(sorted(HERE.glob('*.html')))
        self.assertEqual([], missing)
        self.assertEqual([], broken)
        self.assertGreater(stats['verification-2026-11-05']['rows'],0)

    def test_inherited_links_release_gate(self):
        files = sorted(p for p in b.ROOT.rglob('*.html')
                       if p.relative_to(b.ROOT).parts[0] in b.MODULES
                       and 'data' not in p.relative_to(b.ROOT).parts)
        _,_,broken = b.scan(files)
        self.assertEqual([],broken, f'Broken published local links: {broken[:10]}')

    def test_root_discovery_survives_regeneration(self):
        route = 'verification-2026-11-05/index.html'
        self.assertIn(route, (b.ROOT/'index.html').read_text())
        self.assertIn(route, (b.ROOT/'engine/build.py').read_text())
        self.assertIn('2026-11-05/flagged.html', (b.ROOT/'index.html').read_text())

    def test_spot_checked_score_matches_frozen_extract(self):
        import csv
        with (b.ROOT/'nba-evidence/data/games.csv').open(newline='') as f:
            matches = [r for r in csv.DictReader(f) if r['game_id']=='0022400487']
        self.assertEqual(1, len(matches))
        self.assertEqual(('2025-01-05','BOS','OKC','92','105',b.GAMES),
                         tuple(matches[0][key] for key in ('date','team1','team2','score1','score2','source_url')))

if __name__=='__main__': unittest.main()
