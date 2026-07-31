from statsbombpy import sb
from pathlib import Path
import pandas as pd
import numpy as np

# helper functions
def distance(x, y):
    return np.sqrt((120 - x)**2 + (40-y)**2)

def angle(x, y):
    goal_width = 7.32
    left = np.array([120, 40 - goal_width / 2])
    right = np.array([120, 40 + goal_width / 2])
    shot = np.array([x, y])

    a = np.linalg.norm(shot - left)
    b = np.linalg.norm(shot - right)
    c = goal_width

    # have to do to avoid arccos error
    cos_ang = ((a*a + b*b - c*c) / (2*a*b))

    cos_ang = np.clip(cos_ang, -1.0, 1.0)

    return np.arccos(cos_ang)


def filter_laliga():
    # get all competitions
    competitions = sb.competitions()

    # get la liga from all competitions
    laliga = competitions[competitions['competition_id'] == 11]
    # remove 1973/74 season
    laliga = laliga[laliga['season_id'] != 278]

    return laliga


def get_all_matches(competition_df):
    all_matches = []

    # get all matches from every la liga season in dataset
    for _, row in competition_df.iterrows():
        matches = sb.matches(
            competition_id=row['competition_id'],
            season_id=row['season_id'],
        )
        all_matches.append(matches)

    matches_df = pd.concat(all_matches)
    # remove potential duplicates
    matches_df = matches_df.drop_duplicates(subset=['match_id'])
    return matches_df

def get_all_shots(matches_df):
    # get all shots from every match
    all_shots = []

    for match_id in matches_df['match_id']:
        try:
            events = sb.events(match_id=match_id)
            shots = events[events['type'] == 'Shot']
            all_shots.append(shots)
        except:
            print(f"Failed to get events for {match_id}")

    events_df = pd.concat(all_shots)

    # remove shots with no location data (needed for xG)
    events_df = events_df.dropna(subset=["location"])

    # remove unnecessary columns
    shots_df = events_df.copy()
    shots_df = shots_df.dropna(axis=1, how='all')

    # separate location
    shots_df['x'] = shots_df['location'].apply(lambda l: l[0])
    shots_df['y'] = shots_df['location'].apply(lambda l: l[1])

    # drop location column
    shots_df = shots_df.drop(columns='location')

    # change shot outcome to binary goal
    shots_df['goal'] = shots_df['shot_outcome'].apply(lambda x: 1 if x == 'Goal' else 0)

    # remove shot outcome column and statsbomb xg
    shots_df = shots_df.drop(columns='shot_outcome')
    shots_df = shots_df.drop(columns='shot_statsbomb_xg')

    # get distance to goal
    shots_df['distance'] = shots_df.apply(
        lambda row: distance(row['x'], row['y']), axis=1
    )

    # get angle to goal
    shots_df['angle'] = shots_df.apply(
        lambda row: angle(row['x'], row['y']), axis=1
    )

    return shots_df

def setup_data():
    save_path = Path('resources/shots.csv')

    if (save_path.is_file()):
        print("Data already setup")
        return

    laliga_seasons_df = filter_laliga()
    all_matches_df = get_all_matches(laliga_seasons_df)
    all_shots_df = get_all_shots(all_matches_df)
    all_shots_df.to_csv(save_path, index=False)