#!/usr/bin/env python3
"""Validate generated rental-sf pages, source links, tables, and core calculations."""
from __future__ import annotations

from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
ALLOWED_HOSTS = {
    "www.sf.gov",
    "sf.gov",
    "leginfo.legislature.ca.gov",
    "uscode.house.gov",
    "www.ecfr.gov",
    "ecfr.gov",
}
EXPECTED_PAGES = {
    "index.html",
    "unit-analysis.html",
    "law-and-coverage.html",
    "lawful-paths.html",
    "notice-process.html",
    "owner-practices.html",
    "tenant-help.html",
    "review-checklist.html",
    "repository-audit.html",
    "sources.html",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[dict[str, str | None]] = []
        self.rows: list[list[dict[str, str | None]]] = []
        self.current_row: list[dict[str, str | None]] | None = None
        self.in_tbody = False
        self.h1_count = 0
        self.title_text = False
        self.title = ""
        self.in_title = False
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "a" and "href" in attr:
            self.anchors.append({"href": attr.get("href"), "source": attr.get("data-source")})
            if self.current_row is not None:
                self.current_row.append({"href": attr.get("href"), "source": attr.get("data-source")})
        elif tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.current_row = []
            self.rows.append(self.current_row)
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self.in_title = True
        elif tag == "script":
            self.scripts += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr":
            self.current_row = None
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    html_files = {path.name for path in ROOT.glob("*.html")}
    if html_files != EXPECTED_PAGES:
        fail(f"Unexpected generated page set: {sorted(html_files)}")

    source_ids: set[str] = set()
    source_urls: dict[str, str] = {}
    for page_path in sorted(ROOT.glob("*.html")):
        text = page_path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        if parser.h1_count != 1:
            fail(f"{page_path.name}: expected exactly one h1, got {parser.h1_count}")
        if not parser.title.strip():
            fail(f"{page_path.name}: missing title")
        if parser.scripts:
            fail(f"{page_path.name}: external or inline scripts are not expected")

        for anchor in parser.anchors:
            href = anchor["href"] or ""
            source_id = anchor["source"]
            parsed = urlparse(href)
            if parsed.scheme in {"https", "http"}:
                if parsed.scheme != "https":
                    fail(f"{page_path.name}: external link is not HTTPS: {href}")
                host = (parsed.hostname or "").lower()
                if host not in ALLOWED_HOSTS:
                    fail(f"{page_path.name}: external link is not an approved official host: {href}")
                if not source_id:
                    fail(f"{page_path.name}: external source link lacks a source ID: {href}")
                if source_id in source_urls and source_urls[source_id] != href:
                    fail(f"{page_path.name}: source ID {source_id} points to inconsistent URLs")
                source_ids.add(source_id)
                source_urls[source_id] = href
            elif parsed.scheme or href.startswith("//"):
                fail(f"{page_path.name}: unsupported link scheme: {href}")
            else:
                local_target = href.split("#", 1)[0]
                if local_target:
                    target = (ROOT / local_target).resolve()
                    if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                        fail(f"{page_path.name}: local link escapes rental-sf: {href}")
                    if not target.exists():
                        fail(f"{page_path.name}: broken local link: {href}")

        for row_number, row in enumerate(parser.rows, start=1):
            row_sources = [anchor for anchor in row if anchor["source"]]
            if not row_sources:
                fail(f"{page_path.name}: table row {row_number} has no official-source link")

    # The source register itself is generated from this exact set; requiring every ID
    # to appear in rendered HTML catches unused or accidentally omitted sources.
    from build import SOURCES  # local import keeps source registry as the single source of truth

    expected_ids = set(SOURCES)
    if source_ids != expected_ids:
        fail(f"Source IDs differ. Missing={sorted(expected_ids - source_ids)}, extra={sorted(source_ids - expected_ids)}")

    unit_text = (ROOT / "unit-analysis.html").read_text(encoding="utf-8")
    required_phrases = [
        "13.1%",
        "$412.65",
        "$63.92",
        "$50.40",
        "2020 freeze history",
        "February 28, 2027",
        "Blank — unverified",
        "identities omitted",
    ]
    for phrase in required_phrases:
        if phrase not in unit_text:
            fail(f"unit-analysis.html is missing required caveat/calculation: {phrase}")

    if Decimal("3995") * Decimal("0.016") != Decimal("63.920"):
        fail("Unit A arithmetic mismatch")
    if Decimal("3150") * Decimal("0.016") != Decimal("50.400"):
        fail("Unit B annual-only arithmetic mismatch")
    if Decimal("3150") * Decimal("0.131") != Decimal("412.650"):
        fail("Unit B conditional cumulative arithmetic mismatch")

    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    if any(token in css.lower() for token in ("localhost", "127.0.0.1", "http://")):
        fail("CSS contains a local or insecure external reference")
    if not (ROOT / ".nojekyll").exists():
        fail("Missing .nojekyll file")

    print(f"PASS: {len(html_files)} pages; {len(source_ids)} official sources; all table rows linked; internal links valid.")
    print("PASS: conditional arithmetic, date boundary, privacy labels, HTTPS, and static/no-script checks.")


if __name__ == "__main__":
    main()
