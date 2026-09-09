

def get_team_record(data):
    """
    :param data: dict of team's season stats
    :return: team's record in format of W-D-L
    """
    wins = data["record"]["wins"]
    draws = data["record"]["draws"]
    losses = data["record"]["losses"]

    return wins, draws, losses

def get_team_points(data):
    return data["record"]["points"]

def get_team_goals(data):
    """
    :param data: dict of team's season stats
    :return: team's goals for and against
    """
    g_for = data["totals"]["goals_for"]
    g_against = data["totals"]["goals_against"]
    return g_for, g_against

def get_attack_frame(data):
    g_for = data["totals"]["goals_for"]
    xG = data["totals"]["xg_for"]
    shots = data["totals"]["shots"]
    big_chances = data["totals"]["big_chances"]
    return {"Goals For": [g_for], "Expected Goals": [xG], "Shots": [shots],
            "Big Chances": [big_chances]}

def get_defense_frame(data):
    g_against = data["totals"]["goals_against"]
    xGA = data["totals"]["xg_against"]
    #clean_sheets = data["totals"]["clean_sheets"]
    tackles = data["totals"]["tackles"]
    interceptions = data["totals"]["interceptions"]
    return {"Goals Against": [g_against], "Expected Goals Against": [xGA], "Tackles": [tackles],
            "Interceptions": [interceptions]}

def get_most_recent_matches(data):
    matches = data["matches"]
    most_recent = matches[-5:]
    return most_recent

def get_recent_results(data):
    matches = get_most_recent_matches(data)
    results = {"Opponent": [], "Result": [], "Score": []}
    for match in matches:
        results["Opponent"].append(match["opponent_name"])
        results["Result"].append(match["result"])
        results["Score"].append(match["score"])

    return results
