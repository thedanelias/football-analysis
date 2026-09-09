"""
API:
    get_competition_id_by_name(competition_name) -> gets id of competition from its name
    get_season_id_by_name(season_name) -> gets id of season from its name
"""


import pandas as pd
from scripts.data_loader import ROOT


def get_competition_id_by_name(competition_name):
    competitions_csv = ROOT / "resources" / "statsbomb_team_seasons.csv"
    if competitions_csv.exists():
        competitions = pd.read_csv(competitions_csv)
        hit = competitions[
            competitions["competition_name"].str.lower() == str(competition_name).strip().lower()
        ]
        if not hit.empty:
            return int(hit.iloc[0]["competition_id"])

def get_season_id_by_name(season_name, competition_id=None):
    seasons_csv = ROOT / "resources" / "statsbomb_team_seasons.csv"
    if seasons_csv.exists():
        seasons = pd.read_csv(seasons_csv)
        season_name = str(season_name).strip().lower()
        hit = seasons[seasons["season_name"].str.lower() == season_name]
        if competition_id is not None:
            hit = hit[hit["competition_id"] == int(competition_id)]
        if not hit.empty:
            return int(hit.iloc[0]["season_id"])