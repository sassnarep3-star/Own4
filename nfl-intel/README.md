# nfl-intel/ — NFL Intelligence workspace (session arena/8184197d-own4, 2026-11-12)

Self-contained namespace: **no peer files touched.** Static dashboard + reproducible engine + verified official-source data.

- **Live site:** https://sassnarep3-star.github.io/Own4/nfl-intel/ (after Pages deploy)
- **Reproduce:** `python3 nfl-intel/engine/analyze.py && python3 nfl-intel/engine/build_site.py && python3 nfl-intel/engine/verify_site.py`
- **Data contract:** official NFL.com sources only; every table row links to its source; unverified values blank + flagged (`pages/flagged.html`).
- **Not wagering advice.** NCPG Helpline 1-800-MY-RESET.
- **Entry points:** `index.html` (site) · `EXECUTIVE_SUMMARY.md` · `REPO_REVIEW.md` · `data/` (JSON) · `engine/` (Python stdlib).
