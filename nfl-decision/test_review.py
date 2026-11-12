import importlib.util
import math
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pricing', ROOT / 'pricing.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
spec = importlib.util.spec_from_file_location('build', ROOT / 'build.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr': self.row = []
        if tag == 'a':
            url = attrs.get('href', '')
            self.links.append(url)
            if self.row is not None: self.row.append(url)
    def handle_endtag(self, tag):
        if tag == 'tr': self.rows.append(self.row); self.row = None

class ReviewTests(unittest.TestCase):
    def test_pages_are_current_and_have_sources_and_valid_local_links(self):
        for name, data in b.pages.items():
            with self.subTest(page=name):
                content = (ROOT/name).read_text(encoding='utf-8')
                self.assertEqual(content, b.render(name, data))
                parser = Parser(); parser.feed(content)
                for row in parser.rows[1:]:
                    self.assertTrue(any(u.startswith('https://') for u in row), row)
                for url in parser.links:
                    parts = urlsplit(url)
                    if not parts.scheme and parts.path:
                        self.assertTrue((ROOT / unquote(parts.path)).exists(), url)
    def test_binary_joint_and_feasible_bounds(self):
        self.assertAlmostEqual(p.joint_binary(.5, .5, 0), .25)
        self.assertAlmostEqual(p.joint_binary(.5, .5, 1), .5)
        self.assertAlmostEqual(p.joint_binary(.5, .5, -1), 0)
        with self.assertRaises(ValueError): p.joint_binary(.9, .1, 1)
        with self.assertRaises(ValueError): p.joint_binary(1, .5, 0)
        with self.assertRaises(ValueError): p.joint_binary(.5, .5, math.nan)
    def test_push_fair_price_and_expected_net(self):
        odds = p.fair_decimal(.4, .5)
        self.assertAlmostEqual(odds, 2.25)
        self.assertAlmostEqual(p.expected_net(.4, .5, odds), 0)
        for win, loss in [(0, .5), (.8, .3), (.5, -.1), (math.nan, .3)]:
            with self.assertRaises(ValueError): p.fair_decimal(win, loss)
        with self.assertRaises(ValueError): p.expected_net(.4, .5, math.inf)

if __name__ == '__main__': unittest.main()
