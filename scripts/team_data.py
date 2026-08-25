from data_loader import load_events
from pathlib import Path
import csv
from data_loader import ROOT

def get_team_events(match_id, team):
    events = load_events(match_id)
    return events[events["team"] == team]

def team_stats(match_id, team):
    events = get_team_events(match_id, team)

    goals = len(
        events[
            events["shot_outcome"] == "Goal"
        ])

    shots = len(
        events[
            events["type"] == "Shot"
        ]
    )

    passes = len(
        events[
            (events["type"] == "Pass") &
            (events["pass_outcome"].isna())
        ]
    )

    return {
        "goals": goals,
        "shots": shots,
        "passes": passes
    }

def get_seasons(team):
    seasons = {}
    id_str = str(team)
    path = ROOT / "resources" / "statsbomb_team_seasons.csv"
    with path.open("r", newline="", encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            if row[0] == id_str:
                seasons[row[4] + "," + row[2]] = row[5] + " " + row[3]
    return seasons