"""Reproducible NFL assurance pipeline; expanded as source snapshots arrive."""
import argparse
import py_compile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
py_compile.compile(str(ROOT / 'fetch_official.py'), doraise=True)
print('Acquisition implementation compiles; full release audit is not yet complete.')
