#!/bin/bash
# Regenerate every artefact in this workspace, in dependency order, then build the site and gate it.
set -e
cd "$(dirname "$0")/../.."
python3 nfl-live-board/engine/reconcile.py
python3 nfl-live-board/engine/originate.py
python3 nfl-live-board/engine/leaderboard.py
python3 nfl-live-board/engine/correlations.py
python3 nfl-live-board/engine/availability.py
python3 nfl-live-board/engine/context.py
python3 nfl-live-board/engine/requirements.py
python3 nfl-live-board/engine/audit_repo.py
python3 nfl-live-board/build.py
python3 nfl-live-board/verify.py
