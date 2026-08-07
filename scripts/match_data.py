from data_loader import load_events

def get_match_events(match_id):
    return load_events(match_id)

def get_shots(match_id):
    events = get_match_events(match_id)
    return events[events["type"] == "Shot"]

def get_passes(match_id):
    events = get_match_events(match_id)
    return events[events["type"] == "Pass"]

def get_match_score(match_id):
    shots = get_shots(match_id)
    goals = shots[shots["shot_outcome"] == "Goal"]
    return goals.groupby("team").size()