# REPO_REVIEW.md — Line-by-Line Repository Review

**Review date:** 2026-11-02 (UTC) · **Starting commit:** `319d6b05a6ff2b3d05d82cd313b69d61e72afb50`
**Branch under review:** `arena/3ab8432d-own4` · **Remote:** <https://github.com/sassnarep3-star/Own4>

The instruction was to review the repo line by line, verify from official trusted sources, provide
links for manual review, and flag irregularities. At the start of this session the repository
contained exactly one file.

## Files present at start

| # | File | Size / content | Manual-review link (official repo host) | Finding |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | 6 bytes, text `NBA\n` | [github.com/sassnarep3-star/Own4/blob/main/README.md](https://github.com/sassnarep3-star/Own4/blob/main/README.md) | Stub only; no project description, no sources, no verification policy |
| 2 | `.git/` | Git metadata, 1 commit, branch `arena/3ab8432d-own4` | [github.com/sassnarep3-star/Own4/commits/main](https://github.com/sassnarep3-star/Own4/commits/main) | Single "Initial commit"; no prior work to verify |
| 3 | `COORDINATION.md` | **Absent** | [github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md) | Required shared task board did not exist — created by T00 |
| 4 | `.nojekyll`, site files, CI | **Absent** | [github.com/sassnarep3-star/Own4/tree/main](https://github.com/sassnarep3-star/Own4/tree/main) | No site, no build, no Pages workflow, no license, no ignore file |

## GitHub Pages configuration (verified from the official GitHub API)

| Setting | Value | Official API link |
| --- | --- | --- |
| Pages status | `built` | [api.github.com/repos/sassnarep3-star/Own4/pages](https://api.github.com/repos/sassnarep3-star/Own4/pages) |
| Public URL | `https://sassnarep3-star.github.io/Own4/` | [sassnarep3-star.github.io/Own4/](https://sassnarep3-star.github.io/Own4/) |
| Source | `main` branch, path `/` | [api.github.com/repos/sassnarep3-star/Own4/pages](https://api.github.com/repos/sassnarep3-star/Own4/pages) |
| Build type | `legacy` (Jekyll) | [api.github.com/repos/sassnarep3-star/Own4/pages](https://api.github.com/repos/sassnarep3-star/Own4/pages) |
| HTTPS enforced | `true` | [api.github.com/repos/sassnarep3-star/Own4/pages](https://api.github.com/repos/sassnarep3-star/Own4/pages) |
| Default branch | `main` | [api.github.com/repos/sassnarep3-star/Own4](https://api.github.com/repos/sassnarep3-star/Own4) |

Because Pages was already enabled on `main /` with a **legacy Jekyll build**, this project adds a
`.nojekyll` file so the plain HTML/CSS/JS site is served verbatim instead of being processed by
Jekyll (which ignores underscore-prefixed paths and can rewrite/omit assets).

## Irregularities flagged for review

| ID | Severity | Observation | Official source / manual-review link | Action |
| --- | --- | --- | --- | --- |
| IR-01 | Medium | Repository was a 6-byte stub with no requirements, sources, license, CI or verification policy; nothing could be validated from it. | [README at main](https://github.com/sassnarep3-star/Own4/blob/main/README.md) | Rebuilt README, added `REQUIREMENTS.md`, `SOURCES.md`, `VERIFICATION.md`, `COORDINATION.md` |
| IR-02 | Medium | `COORDINATION.md` required by the parallel-session protocol was missing. | [COORDINATION.md at main](https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md) | Created and committed as the first action (T00) |
| IR-03 | Medium | GitHub Pages uses `legacy` Jekyll build from `main /` with no `.nojekyll`; a static site with `pages/`, `assets/`, `data/` would be at risk of Jekyll rewriting or omitting files. | [Pages API](https://api.github.com/repos/sassnarep3-star/Own4/pages) | Added `.nojekyll`; site generator emits plain HTML only |
| IR-04 | **High** | **No official market odds / closing lines.** NBA.com games pages expose a "HIDE ODDS" control, but no odds values were present in the retrieved official content. The NBA's own release says official betting data is distributed to *licensed operators*, not published as a free NBA.com feed. | [Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) · [NBA official betting-data release](https://www.nba.com/news/nba-extends-u-s-betting-data-partnerships-with-sportradar-and-genius-sports-group) | All market price, vig/hold, closing-line-value and net-ROI cells are **blank + UNVERIFIED**; strategies requiring them cannot clear validation gates |
| IR-05 | High | The 2026-27 season is only 4–7 games deep per team in this snapshot. Any strategy-level claim is under-powered. | [Standings 2026-27](https://www.nba.com/standings) · [Teams Advanced 2026-27](https://www.nba.com/stats/teams/advanced?Season=2026-27) | Sample-size gate G3 fails; no betting strategy is marked validated |
| IR-06 | Medium | Only **62 of 92** games played in the snapshot window were transcribed from official games pages (dates 2026-10-23 … 2026-11-01). | [Games 2026-10-23](https://www.nba.com/games?date=2026-10-23) · [Games 2026-11-01](https://www.nba.com/games?date=2026-11-01) | Disclosed on the Flagged for Review page; backtest results labelled "partial sample" |
| IR-07 | Low | NBA.com "Game Leaders" links on some games pages end in `/null` (e.g. `.../player/1628369/null`, `.../player/1641783/null`). | [Games 2026-11-01](https://www.nba.com/games?date=2026-11-01) · [Games 2026-10-31](https://www.nba.com/games?date=2026-10-31) | Flagged as an official-site link defect; canonical player URLs used instead in our tables |
| IR-08 | Low | `official.nba.com/rulebook/` returned only the page heading on retrieval; rule text was not available for verification. | [NBA Official Rulebook](https://official.nba.com/rulebook/) | Rules-dependent claims left blank + flagged; tie-break text quoted from NBA.com standings instead |
| IR-09 | Low | Official CDN JSON endpoints (`cdn.nba.com/static/json/...`) returned HTTP 500 on retrieval, so no machine-readable official feed was available. | [scoreboard JSON](https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_20261031.json) · [schedule JSON](https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json) | Manual line-by-line transcription from NBA.com HTML pages; every row carries its source URL |
| IR-10 | Medium | Third-party pages surfaced during research are not official and one showed implausible 2026-27 figures ("Paul George 38.0 PPG", several players at 100% 3P%). | [whynba.com league leaders](https://whynba.com/league-leaders/) · [basketball-reference 2025-26 leaders](https://www.basketball-reference.com/leagues/NBA_2026_leaders.html) | All third-party values excluded from every table; listed in `SOURCES.md` §C |
| IR-11 | Low | Player-season table reports **442 rows**; only the top 8 rows were transcribed. No game-level player logs were obtainable from official free pages, so player-prop fair lines (which need a distribution) cannot be computed. | [Players Traditional 2026-27](https://www.nba.com/stats/players/traditional?Season=2026-27&PerMode=PerGame) | Prop fair-line cells blank + UNVERIFIED; season-average baselines shown as verified inputs |
| IR-12 | Low | Home/away designation for each scheduled game was not exposed in the retrieved official page content. | [Games 2026-11-04](https://www.nba.com/games?date=2026-11-04) | Per-game home-court adjustment left blank + flagged; league-level home win rate is reported separately from official standings |
| IR-13 | Info | The platform pins this session to one branch (`arena/3ab8432d-own4`), so per-session `session-<id>/<task>` branches/worktrees cannot be created. | [COORDINATION.md](https://github.com/sassnarep3-star/Own4/blob/arena/3ab8432d-own4/COORDINATION.md) | Recorded in the board; non-overlapping file scopes used instead; single integration pass at T09 |
| IR-18 | **High** | **Parallel-session collision:** while this session worked, other sessions merged PRs #11–#13 into `main`, publishing a canonical root dashboard that overlaps `index.html`, `pages/*`, `README.md`, `COORDINATION.md`, `EXECUTIVE_SUMMARY.md` and `data/sources.json`. PR #15 was reported `CONFLICTING`. | [Pull requests](https://github.com/sassnarep3-star/Own4/pulls) · [main tree](https://github.com/sassnarep3-star/Own4/tree/main) | Collision resolved without discarding any other session's work: their root tree is taken verbatim; this session's entire dashboard was moved into the non-overlapping `own4-dashboard/` namespace, and a handoff entry appended to the shared root `COORDINATION.md` |

## Verification performed

- Every file in the starting tree was opened and read (1 file).
- GitHub Pages state, default branch, and repository metadata read from the official GitHub REST API.
- Every external claim in this review has a link to an official league or official repository host.
- No value was inferred: where a source did not expose a value (odds, rule text, prop distributions,
  home/away flags), the field is recorded as blank/UNVERIFIED and appears on the Flagged for Review page.

## Irregularities that do NOT block publication

Per the task instructions, flagged irregularities and unverified items are published on the
**Flagged for Review** page and do not block the merge or the site.
