#!/usr/bin/env python3
"""Repoint dead links in legacy-root-dashboard.html to surviving canonical pages.

The 2026-11-02 NBA dashboard kept as a legacy artifact referenced a root
``pages/`` tree that was later consolidated. This maps each archived path to its
current canonical destination so the reachable page has no broken links. The
mapping is recorded on the page itself in the added banner.
"""
import io

PATH = "legacy-root-dashboard.html"

# archived root page -> current canonical destination (all verified to exist)
MAP = {
    "pages/requirements.html": "index.html",
    "pages/data-standings.html": "lab/index.html",
    "pages/data-team-stats.html": "lab/index.html",
    "pages/data-games.html": "lab/index.html",
    "pages/data-players.html": "lab/index.html",
    "pages/lines-single.html": "pages/origination.html",
    "pages/lines-parlays.html": "pages/origination.html",
    "pages/lines-props.html": "pages/origination.html",
    "pages/research-strategies.html": "pages/leaderboard.html",
    "pages/research-validation.html": "pages/gates.html",
    "pages/research-correlations.html": "pages/correlations.html",
    "pages/research-backtest.html": "pages/results.html",
    "pages/competition.html": "pages/leaderboard.html",
    "pages/official-sources.html": "pages/sources.html",
    "pages/repo-audit.html": "verification-2026-11-05/index.html",
    "pages/verification.html": "verification-2026-11-05/index.html",
    "pages/flagged-for-review.html": "pages/flagged.html",
    "pages/summary.html": "pages/executive-summary.html",
    "pages/leaderboard.html": "pages/leaderboard.html",
    "pages/research.html": "pages/leaderboard.html",
    "pages/audit.html": "verification-2026-11-05/index.html",
    "pages/correlations.html": "pages/correlations.html",
    "pages/strategies.html": "pages/origination.html",
    "pages/validation.html": "pages/gates.html",
    "pages/flagged.html": "pages/flagged.html",
    "pages/sources.html": "pages/sources.html",
}

with io.open(PATH, encoding="utf-8") as f:
    html = f.read()

# Apply replacements. Sort by key length desc to avoid partial-prefix collisions
# (e.g. pages/strategies.html vs pages/research-strategies.html are distinct
# strings, but be safe regardless).
for old in sorted(MAP, key=len, reverse=True):
    new = MAP[old]
    if old == new:
        continue
    n = html.count('href="%s"' % old)
    html = html.replace('href="%s"' % old, 'href="%s"' % new)
    # keep the visible "Path" column truthful
    html = html.replace(">%s</a>" % old, ">%s</a>" % new)
    html = html.replace("<td>%s</td>" % old, "<td>%s</td>" % new)
    print("repointed %-34s -> %-34s (href hits=%d)" % (old, new, n))

banner = (
    '<div class="panel warn"><strong>Legacy dashboard (2026-11-02).</strong> '
    'Superseded by the canonical dashboard at <a href="index.html">index.html</a>. '
    "Historical subpages named below were consolidated during final integration; "
    "dead links have been repointed to the current canonical destination "
    "(requirements &rarr; index; data-* &rarr; /lab/; lines-* &rarr; origination; "
    "research-* &rarr; leaderboard/gates/correlations/results; competition &rarr; "
    "leaderboard; official-sources &rarr; sources; repo-audit/verification/audit &rarr; "
    "the 2026-11-05 independent audit; flagged-for-review &rarr; flagged). "
    "Values shown are the archived 2026-11-02 snapshot, not current.</div>"
)
marker = '<h1>NBA Line Origination'
html = html.replace(marker, banner + marker, 1)

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(html)
print("done")
