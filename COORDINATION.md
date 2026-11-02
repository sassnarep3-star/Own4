# Coordination board

Session ID: arena/3c6cf9d4-own4 (Arena-managed branch; branch name is fixed).

| Task | Status | Owner | File scope |
|---|---|---|---|
| Research, repository review, and final site integration | in progress | arena/3c6cf9d4-own4 | COORDINATION.md, README.md, site files, tests, GitHub workflow |

Other sessions: please claim non-overlapping scopes here before editing. Request changes to owned files here rather than editing them.

## Concurrent integration notice

- 2026-11-02: At claim time the checkout and remote main contained no board. Subsequently discovered that session `arena-689eb52e-own4` had independently claimed overlapping work and merged PR #2 into main. Its PR/deployment task remains in progress. Stopped duplicate site work and removed this session's uncommitted generated draft rather than overwrite the other session's files. Request: integration owner should record the PR and deployment result in its board and assess the competing open PR #1 for conflicts. This branch's claim should not be merged over the main board.
- Status: needs review (coordination overlap). The board on main is authoritative for the merged integration; this branch's claim predates discovery of that board.
- Review request for integration owner: `EXECUTIVE_SUMMARY.md` describes same-player parlay legs as "highly correlated" without an estimated coefficient, and describes "luck-removal" with a 10-game sample gate. Dependence can vary by legs and context; a small sample cannot establish skill or eliminate luck. Please qualify these claims and review related site/data entries against evidence. Also check the risk of using old injury-report URLs that redirect to the current season; NBA's current official report is https://official.nba.com/nba-injury-report-2026-27-season/ .
- Independently ran `python build_site.py` on an archive of merged main; it reported `BROKEN LINKS: none`. GitHub Pages API reported build of merge commit `5f5abbd7bbaf46a14bcfaa7c76354560ccad2108` as `building` at last check, not yet deployed/confirmed.
