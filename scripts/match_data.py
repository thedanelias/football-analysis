"""API:
    get_match_events(match_id)  -> raw events df for a match
    get_shots(match_id)         -> clean shot events (team, player, xg, outcome, minute)
    get_passes(match_id)        -> clean pass events (team, player, outcome, type)
    get_teams(match_id)         -> both team names in the match
    get_match_score(match_id)   -> dict {team_name: goals}
"""

from scripts.data_loader import load_events


def _name(value):
    return value.get("name") if isinstance(value, dict) else None


def get_match_events(match_id):
    return load_events(str(match_id))


def _select(events, event_type):
    return events[events["type"].map(_name) == event_type].copy()


def get_shots(match_id):
    shots = _select(get_match_events(match_id), "Shot")
    shots["team_name"] = shots["team"].map(_name)
    shots["player_name"] = shots["player"].map(_name)
    shots["shot_xg"] = shots["shot"].map(lambda d: (d or {}).get("statsbomb_xg", 0.0))
    shots["shot_outcome"] = shots["shot"].map(lambda d: _name((d or {}).get("outcome")))
    shots["shot_type"] = shots["shot"].map(lambda d: _name((d or {}).get("type")))
    return shots


def get_passes(match_id):
    passes = _select(get_match_events(match_id), "Pass")
    passes["team_name"] = passes["team"].map(_name)
    passes["player_name"] = passes["player"].map(_name)
    passes["pass_outcome"] = passes["pass"].map(lambda d: _name((d or {}).get("outcome")))
    passes["pass_completed"] = passes["pass"].map(lambda d: "outcome" not in (d or {}))
    passes["pass_type"] = passes["pass"].map(lambda d: _name((d or {}).get("type")))
    return passes


def get_teams(match_id):
    team_names = []
    for name in get_match_events(match_id)["team"].dropna().map(_name):
        if name and name not in team_names:
            team_names.append(name)
    return team_names


def get_match_score(match_id):
    goals = get_shots(match_id)
    goals = goals[goals["shot_outcome"] == "Goal"]
    return goals.groupby("team_name").size().to_dict()