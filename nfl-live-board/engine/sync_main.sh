#!/bin/bash
# Own4 · nfl-live-board · keep this branch rebased on main while other sessions merge.
# COORDINATION.md is append-only by convention, so a conflict there is resolved by keeping
# BOTH sides (peer block first, this session's block second). Any other conflicted file stops
# the loop and is left for a human read - it is never auto-resolved.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
for _ in 1 2 3 4 5; do
  git fetch -q origin main || exit 2
  if git merge-base --is-ancestor origin/main HEAD; then echo "up to date with main"; exit 0; fi
  if git pull --rebase -q origin main 2>/dev/null; then echo "rebased cleanly"; exit 0; fi
  others=$(git diff --name-only --diff-filter=U | grep -v '^COORDINATION.md$' || true)
  if [ -n "$others" ]; then echo "STOP: non-coordination conflict in: $others"; exit 3; fi
  python3 - <<'PY'
p='COORDINATION.md'
s=open(p).read()
while True:
    i=s.find('<<<<<<< ')
    if i<0: break
    j=s.index('\n=======\n', i); k=s.index('\n>>>>>>> ', j)
    e=s.find('\n', k+1); e=len(s) if e<0 else e
    peer=s[i:j].split('\n',1)[1]
    mine=s[j+len('\n=======\n'):k+1]
    s=s[:i]+peer+'\n'+mine+s[e:]
open(p,'w').write(s)
PY
  git add COORDINATION.md
  GIT_EDITOR=true git rebase --continue >/dev/null 2>&1
  if [ ! -d .git/rebase-merge ] && [ ! -d .git/rebase-apply ]; then echo "resolved and rebased"; exit 0; fi
done
echo "STOP: still rebasing after 5 attempts"; exit 4
