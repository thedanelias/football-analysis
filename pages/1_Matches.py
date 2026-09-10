import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scripts import match_data, player_data, team_data, create_graphs, data_loader
from scripts.create_graphs import plot_pass_map_match

st.set_page_config(
    page_title="Match Analysis",
    layout="wide",
)

st.title("Match Analysis")
st.sidebar.header("Filters")

matches_df = pd.read_csv("resources/statsbomb_matches.csv")
matches_df["match_id"] = matches_df["match_id"].astype(int)

session_match_id = st.session_state.get("match_id")
if isinstance(session_match_id, pd.Series):
    session_match_id = int(session_match_id.iloc[0])
elif session_match_id is not None:
    session_match_id = int(session_match_id)

preset = None
if session_match_id is not None:
    preselected = matches_df[matches_df["match_id"] == session_match_id]
    if not preselected.empty:
        preset = preselected.iloc[0]

competitions = sorted(matches_df["competition_name"].unique())
competition = st.sidebar.selectbox(
    "Competition",
    competitions,
    index=competitions.index(preset["competition_name"]) if preset is not None else None,
    placeholder="Select Competition",
)

if not competition:
    st.info("Select a match to view its analysis.")
    st.stop()

season_df = matches_df[matches_df["competition_name"] == competition]
seasons = sorted(season_df["season_name"].unique())
season = st.sidebar.selectbox(
    "Season",
    seasons,
    index=seasons.index(preset["season_name"])
    if preset is not None and preset["competition_name"] == competition
    else None,
    placeholder="Select Season",
)

if not season:
    st.info("Select a match to view its analysis.")
    st.stop()

match_df = season_df[season_df["season_name"] == season]
match_labels = (
    match_df["home_team_name"]
    + " vs "
    + match_df["away_team_name"]
    + " ("
    + match_df["match_date"]
    + ")"
)
match_ids = match_df["match_id"].tolist()
match = st.sidebar.selectbox(
    "Match",
    match_labels,
    index=match_ids.index(session_match_id)
    if preset is not None
    and preset["competition_name"] == competition
    and preset["season_name"] == season
    and session_match_id in match_ids
    else None,
    placeholder="Select Match",
)

if not match:
    st.info("Select a match to view its analysis.")
    st.stop()

match_id = match_ids[match_labels.tolist().index(match)]
st.session_state["match_id"] = match_id

row = match_df[match_df["match_id"] == match_id].iloc[0]
home_id, away_id = int(row["home_team_id"]), int(row["away_team_id"])
home_name, away_name = row["home_team_name"], row["away_team_name"]

st.header(f"{home_name} {row['home_score']} - {row['away_score']} {away_name}")
st.caption(f"{row['competition_name']} - {row['season_name']} - {row['match_date']}")

try:
    home_stats = team_data.get_team_match_stats(match_id, home_id)
    away_stats = team_data.get_team_match_stats(match_id, away_id)
except (ValueError, FileNotFoundError):
    st.error("No event data is available for this match.")
    st.stop()

for team_label, stats in ((home_name, home_stats), (away_name, away_stats)):
    st.markdown(f"**{team_label}**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Possession", f"{stats['possession_pct']}%")
    col2.metric("Shots", stats["shots"])
    col3.metric("xG", stats["xg"])
    col4.metric("Pass Accuracy", f"{stats['pass_accuracy_pct']}%")

st.divider()

left, right = st.columns([1, 1])

def player_match_rows(match_id_f):
    rows = []
    for _, lineup in data_loader.load_lineups(match_id_f).iterrows():
        team_label_f = lineup["team_name"]
        for entry in lineup["lineup"]:
            pid = int(entry["player_id"])
            try:
                stats_f = player_data.player_match_stats(match_id_f, pid)
            except (ValueError, FileNotFoundError):
                continue
            rows.append(
                {
                    "Player": entry["player_name"],
                    "Team": team_label_f,
                    "Passes": stats_f.get("pass_attempts", 0),
                    "Shots": stats_f.get("shots", 0),
                    "Goals": stats_f.get("goals", 0),
                    "xG": round(stats_f.get("total_xg", 0.0), 2),
                }
            )
    return rows

match_rows = player_match_rows(match_id)
match_df = pd.DataFrame(match_rows)
teams = match_df["Team"].unique()

with left:
    team1 = teams[0]
    st.subheader(team1 + "'s Player Stats")
    st.dataframe(match_df[match_df["Team"] == team1].drop(columns=["Team"]))

with right:
    team2 = teams[1]
    st.subheader(team2 + "'s Player Stats")
    st.dataframe(match_df[match_df["Team"] == team2].drop(columns=["Team"]))

st.divider()

shot_timeline = st.columns(1)
with shot_timeline[0]:
    st.subheader("Shot Timeline")

    shots = match_data.get_shots(match_id)
    if not shots.empty:
        timeline = shots[["minute", "shot_xg", "team_name"]].copy()
        timeline = timeline[timeline["shot_xg"] > 0]
        timeline["shot_xg"] = timeline["shot_xg"].round(2)
        if not timeline.empty:
            st.scatter_chart(timeline, x="minute", y="shot_xg", color="team_name")
        else:
            st.info("No shot xG data for this match.")
    else:
        st.info("No shot data for this match.")

st.divider()
bottom_left, bottom_right = st.columns(2)

with bottom_left:
    team = teams[0]
    st.subheader(team + " Passing Map")
    fig_home_pass, ax1 = create_graphs.plot_pass_map_match_team(match_id, team)
    st.pyplot(fig_home_pass)


with bottom_right:
    team = teams[1]
    st.subheader(team + " Passing Map")
    fig_away_pass, ax2 = create_graphs.plot_pass_map_match_team(match_id, team)
    st.pyplot(fig_away_pass)

st.divider()

home_shots_map, away_shots_map = st.columns(2)

with home_shots_map:
    team = teams[0]
    st.subheader(team + " Shots")
    fig_home_shot, ax4 = create_graphs.plot_shot_map_match_team(match_id, team)
    st.pyplot(fig_home_shot)

with away_shots_map:
    team = teams[1]
    st.subheader(team + " Shots")
    fig_away_shot, ax5 = create_graphs.plot_shot_map_match_team(match_id, team)
    st.pyplot(fig_away_shot)