"""Shared helpers for the nfl-consolidated engine (stdlib only)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")


def load(name, base=DATA):
    with open(os.path.join(base, name), "r", encoding="utf-8") as f:
        return json.load(f)


def save(name, obj, base=DATA):
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def save_page(name, html):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
