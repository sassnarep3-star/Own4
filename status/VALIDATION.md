# Validation record — 2026-11-05

Scope: new `status/` entry point, plus selected inherited regression suites.

- `python status/build.py`: 542 files at pinned inherited snapshot a363c75356658db670445bb42541d3c5d30a2298; 144 non-archive static HTML pages. Every UTF-8 file read for line count and SHA-256, not factual verification.
- `python status/test_status.py`: 3 tests pass; every new page's local target exists and every new table row has a primary-domain or official-repository evidence link.
- `cd nba-evidence && python collect_evidence.py`: 57/57 committed-extract consistency checks.
- `cd nba-evidence && python -m unittest discover -s tests -v`: 22 tests pass.
- `cd nba-evidence && python verify_site.py`: 17 pages, 1,041 source-linked rows, 351 local links pass structural checks. External sources not all refetched.
- `cd nba-evidence && python -m nba_lab.analysis`: reproducible output; no tracked changes. 0 qualified strategies. Brier 0.3076264761 vs 0.2719754253 baseline.
- `python -m unittest discover -s tests -v`: 6 inherited tests pass.
- `node tests/engine.test.mjs`: synthetic primitive tests pass.
- `python scripts/verify_data.py`: inherited consistency checks pass; ATL/DAL discrepancies remain flagged, not repaired or newly verified.
- `python scripts/check_site.py`: 11 lab pages, 758 links, 438 rows, no structural problems.

Global mechanical audit: 455 static rows without an audit-allowlisted primary-source link; 2 missing local targets in inherited NFL pages. These are review candidates, not established false claims. No edits made to peer namespaces. The two missing targets are published on the audit page; they do not affect navigation of the new NBA status site.

Fresh primary-source reads through fetch_page: NBA FAQ chunk 0, NBA glossary chunk 0, scikit-learn calibration chunk 0, entire NIST covariance page, BOS/OKC Jan 5 2025 box-score chunks 0 and 3. Only visible passages support claims. No full source-corpus revalidation or legal data permission is asserted. The initial network warning in coordination was conservative; page-fetch tools succeeded for these targeted sources despite shell outbound restrictions.

Concurrent integration: main advanced through PR #34 during this audit; PR #35 is another isolated verification/coordination contribution. This session preserves those changes and remains scoped to status/ and appended coordination records. No competing root dashboard is introduced.
