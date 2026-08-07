import pandas as pd
import json
from pathlib import Path

DATA_PATH = Path("statsbomb_data")

def load_events(match_id):
    return pd.read_json(DATA_PATH / "events" / f"{match_id}.json")

def load_lineups(match_id):
    return pd.read_json(DATA_PATH / "lineups" / f"{match_id}.json")

def load_matches(competition_id, season_id):
    return pd.read_json(DATA_PATH / "matches" / str(competition_id) / f"{season_id}.json")

def load_competitions():
    with open(DATA_PATH / "competitions.json") as f:
        return pd.DataFrame(json.load(f))