# football-analysis

A [Streamlit](https://streamlit.io/) web app for browsing match, team and player statistics. Built on the [StatsBomb Open Data](https://github.com/statsbomb/open-data) dataset.

## Project overview

The project has two loosely connected halves:

- **`scripts/`: data pipeline.** Retrieves the StatsBomb open-data dataset, and provides an API for generating CSVs of matches, players, and teams. Also implements a baseline logistic regression xG model and a hierarchical Bayesian player-adjusted xG model (PyMC MCMC) that isn't in use.
- **`app.py` + `pages/`: Streamlit multipage UI.** Browse competitions/seasons/matches, drill into per-match team and player stats, and view pass maps and shot maps. Pages are auto-discovered by their numbered filename prefix (`1_Matches.py`, `2_Players.py`, `3_Teams.py`).

## Repository structure

```
app.py                     Streamlit entry point (home page)
pages/                     Streamlit multipage UI (matches, players, teams)
reports/                   Published reports (e.g. player_based_xg.pdf)
scripts/
  data_loader.py           Reads local StatsBomb open-data JSON (app/backend scripts)
  get_matches.py           Generates resources/statsbomb_matches.csv
  get_players_and_teams.py Generates player/team/season CSVs from lineups + matches
  match_data.py            Match event helpers (shots, passes, teams, score)
  team_data.py             Team match/season statistics
  player_data.py           Player match/season statistics
  create_graphs.py         mplsoccer pass maps and shot maps
  seasons_competitions_data.py / parse_team_stats_season.py  small data helpers
statsbomb_data/            Local StatsBomb open-data dataset (see below)
resources/                 Generated outputs (CSVs, model trace, figures) — untracked
```

Any files not listed above are currently not in use and/or deprecated.

## Dependencies

There is currently no `requirements.txt` or lockfile. The dependencies are:

| Package          | Used for                                        |
|------------------|-------------------------------------------------|
| `pandas`         | Data wrangling                                  |
| `streamlit`      | Web app UI                                      |
| `mplsoccer`      | Pitch pass/shot maps in the web app             |

Install them with:

```bash
pip install pandas streamlit mplsoccer
```

Python 3.10+ is required.

## Downloading the StatsBomb open-data dataset

The web app reads local StatsBomb open-data JSON from `statsbomb_data/` at the repo root. The dataset is not versioned in this repo, so you need to fetch it yourself.

1. Clone the StatsBomb open-data repository:

   ```bash
   git clone https://github.com/statsbomb/open-data.git
   ```

2. Copy the **contents** (not the folder itself) of the downloaded repo into `statsbomb_data/` in this project root:

   ```bash
   # results in statsbomb_data/competitions.json, statsbomb_data/events/, etc.
   xcopy /E /I "open-data\events"   "football-analysis\statsbomb_data\events"
   xcopy /E /I "open-data\lineups"  "football-analysis\statsbomb_data\lineups"
   xcopy /E /I "open-data\matches"  "football-analysis\statsbomb_data\matches"
   xcopy /E /I "open-data\three-sixty" "football-analysis\statsbomb_data\three-sixty"
   copy "open-data\competitions.json" "football-analysis\statsbomb_data\competitions.json"
   ```

   (On macOS/Linux, use `cp -r` instead of `xcopy`.) After this, `statsbomb_data/` must look like:

   ```
   statsbomb_data/
     competitions.json
     events/{match_id}.json
     lineups/{match_id}.json
     matches/{competition_id}/{season_id}.json
     three-sixty/{match_id}.json
   ```

Alternatively, clone the open-data repo directly into `statsbomb_data/` and delete its `README` and `LICENSE`:

```bash
git clone https://github.com/statsbomb/open-data.git statsbomb_data
```

The dataset is licensed under the CC BY 4.0 licence — always credit StatsBomb when using it.

## Web app

Before starting the app, generate the searchable CSVs it reads from `resources/`:

```bash
python scripts/get_matches.py
python scripts/get_players_and_teams.py
```

Then run:

```bash
streamlit run app.py
```

## Notes

- Scripts inside `scripts/` import each other as flat modules, so always invoke them by path (e.g. `python scripts/main.py`), never as a package.
- `resources/` holds generated outputs and should not be committed.