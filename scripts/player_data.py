from data_loader import load_events, ROOT
import csv

def get_player_events(match_id, player):
    events = load_events(match_id)
    return events[events["player"] == player]

def player_stats(match_id, player):
    events = get_player_events(match_id, player)

    completed_passes = len(
        events[
            (events["type"] == "Pass") &
            (events["pass_outcome"].isna())
        ]
    )

    shots = len(
        events[
            (events["type"] == "Shot")
        ]
    )

    goals = len(
        events[
            (events["shot_outcome"] == "Goal")
        ]
    )

    return {
        "passes": completed_passes,
        "shots": shots,
        "goals": goals
    }

def get_seasons(player):
    seasons = {}
    id_str = str(player)
    path = ROOT / "resources" / "statsbomb_player_seasons.csv"
    with path.open("r", newline="", encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            if row[0] == id_str:
                seasons[row[6] + "," + row[4]] = row[7] + " " + row[5]
    return seasons

print(get_seasons(2947))