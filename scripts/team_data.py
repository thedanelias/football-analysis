from data_loader import load_events

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