# SF Outer Sunset (ZIP 94122) Rent Increase Compliance Dashboard (`sf-rent-94122/`)

Clean, deterministic, multi-page static research dashboard analyzing lawful and standard rental increases for two anonymized units in an owner-reported 1940 San Francisco Outer Sunset (`94122`) residential property as of **November 6, 2026**.

## Pages Generated (`build_site.py`)

- `index.html` — Overview Dashboard (KPI cards, Unit 1 & Unit 2 snapshot, core answers, category tiles)
- `executive-summary.html` — Executive Summary & 6-step compliance action plan
- `units-analysis.html` — Unit 1 & Unit 2 arithmetic, interactive integer-cent calculator, Form 571 schedule (2019–2028), Unit 2 banking scenarios, and ZIP 94122 / HUD FY 2027 benchmarks
- `laws-and-caps.html` — Local SF, California, and Federal statutory matrix + passthroughs & fees
- `landlord-practices.html` — Corporate REITs vs. Individual SF Property Owners
- `notice-and-scrutiny.html` — 5-step notice protocol, valid/invalid reasons, One-vs-Both units matrix, 12-point SF tenant-lawyer audit checklist, and official free legal directory
- `repo-audit.html` — Line-by-line audit of `sassnarep3-star/Own4` (including HTTP 404 link detection in peer `rental-sf/index.html`)
- `sources.html` — 38 allowlisted official government & repository sources verified on `2026-11-06`
- `flagged.html` — 12 non-blocking Flagged for Review items (all unconfirmed values left strictly blank `""`)

## Build & Verify

```bash
python3 sf-rent-94122/build_site.py
python3 sf-rent-94122/verify_site.py
python3 -m unittest discover -s sf-rent-94122 -p "test_*.py" -v
```
