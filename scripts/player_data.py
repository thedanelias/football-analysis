from data_loader import load_events

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