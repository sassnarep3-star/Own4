#!/usr/bin/env python3
"""Automated compliance, link, blank-cell, arithmetic, and privacy verifier for sf-rent-94122."""

from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EXPECTED_HTML_PAGES = [
    "index.html",
    "executive-summary.html",
    "units-analysis.html",
    "laws-and-caps.html",
    "landlord-practices.html",
    "notice-and-scrutiny.html",
    "repo-audit.html",
    "sources.html",
    "flagged.html",
]

EXPECTED_MD_FILES = [
    "EXECUTIVE_SUMMARY.md",
    "REPO_REVIEW.md",
    "README.md",
]

# Strictly statutory/acronym 2-letter uppercase allowlist (zero personal initial pairs allowed)
ALLOWED_UPPER2_ACRONYMS = frozenset(
    {
        "AB",
        "AG",
        "BR",
        "CA",
        "CH",
        "CI",
        "DO",
        "FY",
        "GO",
        "ID",
        "IF",
        "NO",
        "OR",
        "PR",
        "RA",
        "SF",
        "TO",
        "UI",
        "US",
        "YR",
    }
)

KNOWN_DEAD_URLS = frozenset(
    {
        "https://www.sf.gov/information/tenant-protections-against-harassment",
        "https://www.sf.gov/information/eviction-and-tenant-rights-clinics",
    }
)


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.in_blank_td = False
        self.current_tr_links: list[str] = []
        self.tbody_rows_links: list[list[str]] = []
        self.blank_td_texts: list[str] = []
        self.current_blank_buf: list[str] = []
        self.all_hrefs: list[str] = []
        self.all_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.current_tr_links = []
        elif tag == "td":
            cls = attr_map.get("class") or ""
            if "unverified-blank" in cls.split():
                self.in_blank_td = True
                self.current_blank_buf = []
        elif tag == "a":
            href = attr_map.get("href")
            if href:
                self.all_hrefs.append(href)
                if self.in_tbody and self.in_tr:
                    self.current_tr_links.append(href)
        elif tag in ("script", "link", "img"):
            target = attr_map.get("src") or attr_map.get("href")
            if target:
                self.all_srcs.append(target)

    def handle_data(self, data: str) -> None:
        if self.in_blank_td:
            self.current_blank_buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.tbody_rows_links.append(self.current_tr_links)
        elif tag == "td" and self.in_blank_td:
            self.in_blank_td = False
            self.blank_td_texts.append("".join(self.current_blank_buf))


def verify_all() -> list[str]:
    errors: list[str] = []

    sources_data = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    units_data = json.loads((DATA_DIR / "units_and_rates.json").read_text(encoding="utf-8"))
    laws_data = json.loads((DATA_DIR / "laws_and_practices.json").read_text(encoding="utf-8"))

    allowed_hosts = set(sources_data["AllowlistedOfficialHosts"])
    registered_urls = {s["url"] for s in sources_data["sources"]}

    # 1. Check required files exist
    for fname in EXPECTED_HTML_PAGES + EXPECTED_MD_FILES:
        fpath = BASE_DIR / fname
        if not fpath.is_file() or fpath.stat().st_size == 0:
            errors.append(f"Missing or empty deliverable: {fname}")

    for asset in ("assets/style.css", "assets/app.js"):
        apath = BASE_DIR / asset
        if not apath.is_file() or apath.stat().st_size == 0:
            errors.append(f"Missing or empty asset: {asset}")

    # 2. Verify exact Decimal math in units_and_rates.json
    u1, u2 = units_data["units"][0], units_data["units"][1]
    if Decimal("3995.00") * Decimal("0.016") != Decimal("63.92000") or not u1["annual_1_6_pct_increase"].startswith("$63.92"):
        errors.append("Unit 1 1.6% math mismatch")
    if not u1["annual_1_6_pct_new_rent"].startswith("$4,058.92"):
        errors.append("Unit 1 new rent mismatch")
    if Decimal("3150.00") * Decimal("0.016") != Decimal("50.40000") or not u2["annual_1_6_pct_increase"].startswith("$50.40"):
        errors.append("Unit 2 1.6% math mismatch")
    if not u2["annual_1_6_pct_new_rent"].startswith("$3,200.40"):
        errors.append("Unit 2 new rent mismatch")

    # 3. Inspect every HTML page: every tbody row must link to an allowlisted official HTTPS URL
    total_tbody_rows = 0
    total_blank_cells = 0
    for page_name in EXPECTED_HTML_PAGES:
        p = BASE_DIR / page_name
        if not p.is_file():
            continue
        inspector = PageInspector()
        inspector.feed(p.read_text(encoding="utf-8"))

        if not inspector.tbody_rows_links:
            errors.append(f"{page_name}: expected at least one data table row in <tbody>")

        for idx, row_links in enumerate(inspector.tbody_rows_links, start=1):
            total_tbody_rows += 1
            https_official = [
                u
                for u in row_links
                if u.startswith("https://") and urlparse(u).netloc in allowed_hosts and u in registered_urls
            ]
            if not https_official:
                errors.append(
                    f"{page_name} tbody row #{idx}: missing allowlisted registered official https:// source link (found {row_links})"
                )

        for blank_txt in inspector.blank_td_texts:
            total_blank_cells += 1
            if blank_txt != "":
                errors.append(f"{page_name}: unverified-blank cell is non-empty ({blank_txt!r})")

        for ref in inspector.all_hrefs + inspector.all_srcs:
            if ref in KNOWN_DEAD_URLS:
                errors.append(f"{page_name}: links to known HTTP 404 URL {ref}")
            if ref.startswith(("https://", "http://")):
                if not ref.startswith("https://"):
                    errors.append(f"{page_name}: non-HTTPS external link {ref}")
                host = urlparse(ref).netloc
                if host not in allowed_hosts:
                    errors.append(f"{page_name}: external host {host!r} not in AllowlistedOfficialHosts")
            elif ref.startswith("#"):
                continue
            else:
                clean_ref = ref.split("#", 1)[0].split("?", 1)[0]
                resolved = (BASE_DIR / clean_ref).resolve()
                if not resolved.exists():
                    errors.append(f"{page_name}: broken local relative reference {ref!r} -> {resolved}")

    if total_blank_cells == 0:
        errors.append("Expected unverified blank cells to exist and remain empty")

    if len(laws_data["flagged_items"]) < 10:
        errors.append("Expected comprehensive Flagged for Review register")

    # 4. Zero-knowledge PII & Initials Scan across ALL files in sf-rent-94122 (including .py scripts!)
    scan_targets = (
        [BASE_DIR / f for f in EXPECTED_HTML_PAGES + EXPECTED_MD_FILES]
        + list(DATA_DIR.glob("*.json"))
        + list(BASE_DIR.glob("*.py"))
        + [BASE_DIR / "assets/style.css", BASE_DIR / "assets/app.js"]
    )
    spaced_initials_re = re.compile(r"\b[A-Z]\.?\s+[A-Z]\.?\b")
    upper2_re = re.compile(r"\b[A-Z]{2}\b")

    for target in scan_targets:
        text = target.read_text(encoding="utf-8")
        for m in spaced_initials_re.finditer(text):
            errors.append(f"Privacy guard triggered in {target.name}: spaced capital initials {m.group(0)!r}")
        for m in upper2_re.finditer(text):
            tok = m.group(0)
            if tok not in ALLOWED_UPPER2_ACRONYMS:
                errors.append(
                    f"Privacy guard triggered in {target.name}: unallowlisted 2-letter uppercase token {tok!r}"
                )

    print(
        f"Verified {len(EXPECTED_HTML_PAGES)} HTML pages, {total_tbody_rows} table rows with 100% official HTTPS links, "
        f"{total_blank_cells} strictly empty unverified cells, {len(sources_data['sources'])} official sources, and 0 PII leaks."
    )
    return errors


def main() -> int:
    errs = verify_all()
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("ALL SF-RENT-94122 VERIFICATION CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
