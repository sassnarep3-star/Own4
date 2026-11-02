# NBA Evidence

Evidence-first NBA line-origination pilot. Open `site/index.html` or the published GitHub Pages workspace.

## Reproduce

Python 3.11+, standard library only:

```sh
python collect_evidence.py
python -m unittest discover -s tests -v
python -m nba_lab.analysis
python audit_repo.py
python build_site.py
python verify_site.py
```

Run from this directory. `audit_repo.py` scans the enclosing Git checkout without editing peer files. The static site is committed so legacy root-based Pages can serve it without a build step.

## Read first

- `docs/EXECUTIVE_SUMMARY.md`
- `docs/METHODOLOGY.md`
- `docs/REQUIREMENTS.md`
- `docs/SOURCES.md`
- `site/flagged.html`

No validated betting edge, official historical market prices, personalized player forecasts, actual wagers or funded rewards are claimed. Missing values stay null. See the published Flagged for Review page.
