"""Frozen research configuration. Changing any value here changes the trial registry — re-run everything."""
DATASET_REPO = "https://github.com/NocturneBear/NBA-Data-2010-2024.git"
DATASET_COMMIT = "a5f108b5b1f08074d78b9e8e901926a9ce4c06c5"   # pinned; recorded in outputs

DEV_SEASONS = [f"{y}-{str(y+1)[2:]}" for y in range(2010, 2020)]       # 2010-11 .. 2019-20  (fit + threshold choice)
HOLDOUT_SEASONS = [f"{y}-{str(y+1)[2:]}" for y in range(2020, 2024)]   # 2020-21 .. 2023-24  (frozen, evaluated once)

MIN_TEAM_GAMES = 10          # a team needs >=10 prior same-season games (sample-size rule)
MIN_PLAYER_GAMES = 10        # a player needs >=10 prior same-season games played
MIN_PLAYER_MPG = 20.0        # prior season-to-date minutes per game
QUANTILES = [0.50, 0.75, 0.90]   # bet only when |model adjustment| is in the top (1-q) of the dev distribution
EWM_HALFLIFE_GAMES = 5
EWM_HALFLIFE_MIN = 3

LEG_DECIMAL = 1.9091          # ASSUMED standard -110 price per leg (decimal). Breakeven = 1/1.9091 = 52.38%
BREAKEVEN = 1 / LEG_DECIMAL
ALPHA = 0.05

# Gate thresholds (project policy; frozen before the holdout was opened)
MIN_BETS_SINGLE = 1000
MIN_BETS_PARLAY = 300
SIDE_BALANCE = (0.35, 0.65)   # share of Over/Home sides must stay inside this band
PARLAY_MAX_ABS_RHO = 0.10
PARLAY_MAX_LEGS = 3
PLACEBO_RUNS = 300
SEED = 20261102
