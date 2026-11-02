# Own4 — NFL Line Origination & Signal Research

Official-only NFL evidence lab: originate research lines, test singles/parlays/player-prop combinations, measure dependence, and award leaderboard credit only when every validation gate passes.

- **Canonical dashboard:** [GitHub Pages root](https://sassnarep3-star.github.io/Own4/) → `nfl-lab/site/`
- **Executive summary:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- **Flagged for review:** [nfl-lab/site/pages/flagged.html](nfl-lab/site/pages/flagged.html)
- **Source register:** [nfl-lab/site/pages/sources.html](nfl-lab/site/pages/sources.html)
- **Coordination board:** [COORDINATION.md](COORDINATION.md)

## Current evidence boundary

| Entry | Status | Source |
|---|---|---|
| Official NFL final games | 392 rows: 2025 full season + 2026 through Nov 1 | [NFL standings](https://www.nfl.com/standings/league/2026/REG) |
| Walk-forward evaluation | 314 games / 21 season-weeks; future-score perturbation passes | [Temporal validation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) |
| Eligible strategies | 0 — no primary trial survives Holm; market/prospective gates blocked | [Leaderboard](nfl-lab/results/leaderboard.json) |
| Market odds / CLV / ROI | Blank — no verified executable sportsbook archive | [NFL Game Center](https://www.nfl.com/games/bears-at-seahawks-2026-reg-8) |
| Rewards | Virtual badges only; 0 points awarded | [Protocol](nfl-lab/protocol.json) |

## Reproduce

Python 3.11+, standard library only:

```bash
python nfl-lab/collect.py
python nfl-lab/engine.py
python nfl-lab/audit.py
python nfl-lab/build.py
python nfl-lab/tests.py
python nfl-lab/verify.py
python nfl-lab/build.py && python nfl-lab/verify.py
```

The legacy NBA workspace still validates with `python scripts/build.py`, `python -m unittest discover -s tests`, `python scripts/verify_data.py`, and `python scripts/check_site.py`.

## Preserved prior work

This repository previously contained NBA research and parallel NFL contributions. They are preserved, not relabeled as NFL evidence:

- [Legacy NBA README (preserved copy)](nfl-lab/legacy/README_NBA.md)
- [Legacy NBA executive summary (preserved copy)](nfl-lab/legacy/EXECUTIVE_SUMMARY_NBA.md)
- [NFL Quant Lab](nfl-quant/) — separate contribution using third-party historical/market archives
- [NFL specification module](nfl/)
- [Legacy NBA pipeline](pipeline/) and [Data Lab](lab/)

Research only — not wagering advice. No validated edge or funded reward is claimed. National Problem Gambling Helpline: [1-800-MY-RESET](https://www.ncpgambling.org/help-treatment/).
