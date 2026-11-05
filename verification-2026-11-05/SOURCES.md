# Sources, reading scope, and verification log · 2026-11-05

| Primary source | Checked passage | What it does NOT establish |
|---|---|---|
| [NBA Stats FAQ](https://www.nba.com/stats/help/faq) | “Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats” (page fetched and read) | A license for bulk data collection; a historical sportsbook quote; profitability. |
| [NBA games, Jan 5, 2025](https://www.nba.com/games?date=2025-01-05) | Celtics 92; Thunder 105; Final; official game 0022400487. Compared with the single row of `nba-evidence/data/games.csv`. | Any other game row in the repository. |
| [NBA Official Rule No. 5](https://official.nba.com/rule-no-5-scoring-and-timing/) | Regulation periods twelve minutes; overtime periods five minutes. | Sportsbook prop grading, pushes, or cashout policy. |
| [GitHub Pages publishing-source docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) | Branch and folder source can publish a static project site; deployments need confirmation. | That the current PR was deployed (confirm separately using Pages build and live URL). |
| [Repository audit code](https://github.com/sassnarep3-star/Own4/blob/main/verification-2026-11-05/build.py) | Counts are derived by parsing local published HTML only and excluding captured source HTML. | HTTP reachability, source/claim relevance, correctness of data, odds, or skill. |

This is a **bounded** manual primary-source check plus a deterministic structural scan, *not* a claim to have independently rechecked every inherited numeric row. GitHub is the authoritative source for the repository's own code, not for league scores. The root repo contains NBA and NFL pages from prior parallel sessions; all results should retain their own data and methodological labels. All unverifiable values stay blank or are called out on the audit's Flagged for Review page.
