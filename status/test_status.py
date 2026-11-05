"""Structural release checks only; not external truth verification."""
import unittest
from pathlib import Path
from build import Page, resolve, primary, inventory, OUT

class StatusTests(unittest.TestCase):
    def test_local_targets_and_row_sources(self):
        for path in OUT.glob('*.html'):
            p=Page();p.feed(path.read_text())
            for url in p.links:
                target=resolve(path,url)
                if target is not None: self.assertTrue(target.is_file(),(path.name,url))
            for i,row in enumerate(p.rows):
                # Navigation-only pilot links may be accompanied by repository evidence.
                self.assertTrue(any(primary(u) for u in row),(path.name,i,row))
    def test_inventory(self):
        r=inventory()
        self.assertEqual(len(r['files']),542)
        self.assertTrue(all(len(f['sha256'])==64 for f in r['files']))
        self.assertFalse(any(p['path'].startswith('data/raw/') for p in r['pages']))
        self.assertTrue(all(f['factual_status']=='not independently reverified' for f in r['files']))
    def test_url_policy(self):
        self.assertFalse(primary('https://nba.com.evil.example/fake'))
        self.assertFalse(primary('http://nba.com/'))
        self.assertTrue(primary('https://official.nba.com/'))
if __name__=='__main__': unittest.main(verbosity=2)
