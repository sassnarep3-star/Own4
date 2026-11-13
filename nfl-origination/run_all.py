"""Run the whole nfl-origination pipeline in order and stop at the first failure.

    python3 nfl-origination/run_all.py

Order matters: the official transcriptions feed the dataset, the dataset feeds the model, and the
model feeds the site. `verify.py` runs last and is the gate: it exits non-zero if any data row is
unsourced, any local link is broken, or any published claim contradicts the computed evidence.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent

STEPS = [
    ("official standings 2026-11-13", "data/official/standings_2026-11-13.py"),
    ("official Week 10 slate", "data/official/transcribe_slate.py"),
    ("official Week 10 injuries", "data/official/injuries_week10.py"),
    ("dataset + reconciliation", "engine/dataset.py"),
    ("model, backtest, gates", "engine/model.py"),
    ("correlations", "engine/correlations.py"),
    ("own lines + injury band", "engine/originate.py"),
    ("requirements", "data/requirements.py"),
    ("questions", "data/questions.py"),
    ("suggestions", "data/suggestions.py"),
    ("flags + sources", "data/flags.py"),
    ("site build", "build.py"),
    ("verification", "verify.py"),
]


def main():
    for label, script in STEPS:
        print("\n=== %s  (%s) ===" % (label, script))
        r = subprocess.run([sys.executable, str(ROOT / script)], cwd=str(ROOT))
        if r.returncode != 0:
            print("\nFAILED at: %s" % label, file=sys.stderr)
            return r.returncode
    print("\nAll %d steps passed." % len(STEPS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
