import pandas as pd
from mplsoccer import Pitch
# import matplotlib.pyplot as plt
# import numpy as np
from scripts import match_data

def get_pitch():
    return Pitch(
        pitch_type='statsbomb',
        pitch_color='#0b1320',
        line_color='white'
    )

def get_pass_start_and_end(passes_df):
    passes_df[["x", "y"]] = pd.DataFrame(passes_df["location"].tolist(), index=passes_df.index)

    passes_df["end_location"] = passes_df["pass"].apply(
        lambda x: x.get("end_location")
        if isinstance(x, dict)
        else None
    )

    passes_df[["end_x", "end_y"]] = pd.DataFrame(passes_df["end_location"].tolist(), index=passes_df.index)

    return passes_df

def draw_passes(passes_df, pitch):
    fig, ax = pitch.draw(figsize=(12, 8))
    for _, row in passes_df.iterrows():

        if row["pass_completed"]:
            colour = "#00e676"
            alpha = 0.45
        else:
            colour = "#ff7f00"
            alpha = 0.7

        pitch.arrows(
            row["x"],
            row["y"],
            row["end_x"],
            row["end_y"],
            color=colour,
            alpha=alpha,
            width=1.5,
            headwidth=3,
            headlength=3,
            ax=ax
        )

    return fig, ax

def plot_pass_map_match(match_id):
    pitch = get_pitch()
    passes = match_data.get_passes(match_id)
    passes = get_pass_start_and_end(passes)
    return draw_passes(passes, pitch)

def plot_pass_map_match_team(match_id, team_name):
    pitch = get_pitch()
    passes = match_data.get_passes(match_id)
    passes = passes[passes["team_name"] == team_name]
    passes = get_pass_start_and_end(passes)
    return draw_passes(passes, pitch)

def get_shot_location(shots_df):
    shots_df[["x", "y"]] = pd.DataFrame(shots_df["location"].tolist(), index=shots_df.index)
    return shots_df

def draw_shots(shots_df, pitch):
    fig, ax = pitch.draw(figsize=(12, 8))

    # goals
    goals = shots_df[shots_df["shot_outcome"].str.lower() == "goal"]
    misses = shots_df[shots_df["shot_outcome"].str.lower() != "goal"]

    #goals
    pitch.scatter(
            goals["x"],
            goals["y"],
            ax=ax,
            s=goals["shot_xg"] * 1000,
            color="white",
            alpha=0.7,
            edgecolors="white",
            linewidth=2,
            label="goals"
        )

    # misses
    pitch.scatter(
        misses["x"],
        misses["y"],
        ax=ax,
        s=misses["shot_xg"] * 1000,
        color="#ef4444",
        alpha=0.65,
        edgecolors="black",
        linewidth=1,
        label="misses"
    )
    return fig, ax

def plot_shot_map_match_team(match_id, team_name):
    pitch = get_pitch()
    shots = match_data.get_shots(match_id)
    shots = shots[shots["team_name"] == team_name]
    shots = get_shot_location(shots)
    return draw_shots(shots, pitch)