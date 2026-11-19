# nfl-repo-inventory: NFL namespace inventory and verifier audit (2026-11-19)

Session `arena/4f78a318-own4`. Machine-generated map of the 40 `nfl*` namespaces in this
repository, the result of running each verifier on a clean export, and ten flagged
irregularities. It does not re-verify NFL data values.

**Pages:** `index.html` (overview), `pages/inventory.html`, `pages/verifier-runs.html`,
`pages/flagged.html`.

## Reproduce

```
python3 nfl-repo-inventory/engine/collect.py   # reads the repo, writes data/inventory.json
python3 nfl-repo-inventory/engine/build.py     # renders the four pages
python3 nfl-repo-inventory/engine/verify.py    # gate: determinism, links, sources, counts
```

`data/verifier_runs.json` is produced by running each verifier from a clean `git archive`
export, so no verifier writes into the repository. The method is recorded in that file.

## Limits

- The sandbox cannot reach nfl.com through bash. The one official read (2026-11-19, Week 11
  injury report, chunk 0 of 7) went through the fetch tool and is listed in
  `data/official_reads.json` with only the rows that were read.
- A verifier PASS in another namespace means that namespace's links and internal consistency
  were checked. It does not mean its official NFL values were checked (flag F07).
