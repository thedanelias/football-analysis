import pandas as pd
import streamlit as st
from scripts import player_data

st.set_page_config(
    page_title = "Football Analytics",
    page_icon="@",
    layout="wide"
)

st.title("Football Analytics")

match, team, player = st.columns(3)

with match:
    st.subheader("Matches")

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
    competition = st.selectbox(
        "Competition",
        competitions,
        index=competitions.index(preset["competition_name"]) if preset is not None else None,
        placeholder="Select a Competition",
    )

    if competition:
        season_df = matches_df[matches_df["competition_name"] == competition]
        seasons = sorted(season_df["season_name"].unique())
        season = st.selectbox(
            "Season",
            seasons,
            index=seasons.index(preset["season_name"])
            if preset is not None and preset["competition_name"] == competition
            else None,
            placeholder="Select a Season",
        )

        if season:
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
            match = st.selectbox(
                "Match",
                match_labels,
                index=match_ids.index(session_match_id)
                if preset is not None
                and preset["competition_name"] == competition
                and preset["season_name"] == season
                and session_match_id in match_ids
                else None,
                placeholder="Select a Match",
            )

            if match:
                st.session_state["match_id"] = match_ids[match_labels.tolist().index(match)]
                if st.button("Open Match"):
                    st.switch_page("pages/1_Matches.py")

with team:
    st.subheader("Teams")

    teams_df = pd.read_csv("resources/statsbomb_teams.csv")
    teams = sorted(teams_df["team_name"].tolist())

    team_search = st.selectbox("Team:", teams, index=None, placeholder="Search for a team")

    if team_search:
        st.session_state["team_name"] = team_search
        st.switch_page("pages/3_Teams.py")


with player:
    st.subheader("Players")

    players_df = pd.read_csv("resources/statsbomb_players.csv")
    players = sorted(players_df["player_nickname"].fillna(players_df["player_name"]).tolist())

    player_search = st.selectbox("Player:", players, index=None, placeholder="Search for a player")

    if player_search:
        st.session_state["player_id"] = player_data._player_id_from_csv(player_search)
        st.session_state["player_name"] = player_search
        st.switch_page("pages/2_Players.py")

st.divider()

st.subheader("Recent Matches")

st.divider()

st.subheader("Statistics Summary")