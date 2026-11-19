# Executive summary — Week 11 official injury-report delta (2026-11-19)

Scope: one task from the NFL brief — keep dated official injury-report reads and publish the
change between them, not the level. Live site: `nfl-w11-delta/index.html` (served from the repository's Pages site).

**Findings (all from official nfl.com pages; flagged items are listed on the site):**

1. **No designation changed** between the earlier raw capture (2026-11-18 23:49:17Z) and the later read
   (2026-11-19, after 06:48 UTC) for the 242 rows present in both. Source: <https://www.nfl.com/injuries/>.
2. **The Chargers block changed from empty to populated.** The earlier capture printed "No Injuries Reported" for the
   Chargers; the later read shows 11 rows. An empty block is not evidence of health, so the system records block state
   separately from row counts.
3. **Six clubs are absent from both reads** (ATL, CLE, GB, LAR, NE, SEA). "Not listed" is not "available"; bye status
   is not verified here.
4. **Two injury-cell conflicts with official headlines** are flagged, not resolved: Buccaneers QB Baker Mayfield (lower-leg
   injury headline, blank injury cell) and Jets QB Geno Smith (ankle injury in the Week 10 headline, blank injury cell in Week 11).

**Limits:** the later read is a transcription, not raw bytes. Friday's report, which may change game-status designations,
is not read here. Row-level data is in the public repository pending the owner's decision on the private-store term.

**Decision still open:** whether to keep scheduled raw captures (already running Wed/Thu/Fri 18:00 UTC in
`nfl-readiness-register`) as the only source of truth, and whether to move row-level transcripts to a private store.
