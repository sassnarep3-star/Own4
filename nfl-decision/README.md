# NFL decision desk

A static review-first NFL research site, not a live tracking system or a production betting engine. The site proposes options and displays unresolved decisions, official injury-report examples, strategy research candidates, gates, blocked correlations and review flags. It does not certify other NFL namespaces or cover every NFL injury. The 2026-11-12 dated status examples will become stale.

Build and test without external dependencies:

```sh
python3 nfl-decision/build.py
python3 -m unittest discover -s nfl-decision -p 'test_*.py' -v
```

`pricing.py` provides audited-input mathematical primitives only. Its tests use synthetic values, not real lines. It neither fits correlations nor fetches or verifies data, and cannot handle multi-leg, void or correlated-push settlement. The dashboard does not generate live prices. A license-cleared historical price feed, time-stamped official injury/lineup records and independent multi-season out-of-sample evaluation are necessary before operational use.

Source links on proposal rows are methodological or league background, not endorsements of the proposal. Structural tests check table source links and local destinations, not that each external page remains online or supports every claim. Scope of independent source review is documented on the site and in COORDINATION.md.
