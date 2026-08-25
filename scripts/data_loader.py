import pandas as pd
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "statsbomb_data"

def load_events(match_id):
    return pd.read_json(DATA_PATH / "events" / f"{match_id}.json")

def load_lineups(match_id):
    return pd.read_json(DATA_PATH / "lineups" / f"{match_id}.json")

def load_matches(competition_id, season_id):
    return pd.read_json(DATA_PATH / "matches" / str(competition_id) / f"{season_id}.json")

def load_competitions():
    with open(DATA_PATH / "competitions.json") as f:
        return pd.DataFrame(json.load(f))

def flatten_match(raw):
    competition = raw.get("competition") or {}
    season = raw.get("season") or {}
    home_team = raw.get("home_team") or {}
    away_team = raw.get("away_team") or {}
    stage = raw.get("competition_stage") or {}
    stadium = raw.get("stadium") or {}
    referee = raw.get("referee") or {}

    return {
        "match_id": raw.get("match_id"),
        "match_date": raw.get("match_date"),
        "kick_off": raw.get("kick_off"),
        "match_week": raw.get("match_week"),
        "competition_id": competition.get("competition_id"),
        "competition_name": competition.get("competition_name"),
        "season_id": season.get("season_id"),
        "season_name": season.get("season_name"),
        "competition_stage": stage.get("name"),
        "home_team_id": home_team.get("home_team_id"),
        "home_team_name": home_team.get("home_team_name"),
        "home_score": raw.get("home_score"),
        "away_score": raw.get("away_score"),
        "away_team_name": away_team.get("away_team_name"),
        "away_team_id": away_team.get("away_team_id"),
        "stadium": stadium.get("name"),
        "referee": referee.get("name"),
    }

def load_all_matches():
    records = []
    for path in sorted((DATA_PATH / "matches").glob("*/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for match in data:
            records.append(flatten_match(match))
    return pd.DataFrame(records)

def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

