import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title = "Team Analysis",
    layout = "wide"
)

st.title("Team Analysis")

# get team id if selected from homepage
team_name = st.session_state.get("team_name")
team_seasons_df = pd.read_csv("resources/statsbomb_team_seasons.csv")
teams_df = pd.read_csv("resources/statsbomb_teams.csv")

st.sidebar.header("Filters")

teams = sorted(teams_df["team_name"].unique())

team = st.sidebar.selectbox(
    "Team", teams, index=team_name, placeholder="Select Team"
)

team_competitions_df = team_seasons_df[team_seasons_df["team_name"] == team]
competition = st.sidebar.selectbox("Competition", sorted(team_competitions_df["competition_name"].unique()),
                                   index=None, placeholder="Select Competition")

team_seasons_df = team_competitions_df[team_competitions_df["competition_name"] == competition]
season = st.sidebar.selectbox("Season", sorted(team_seasons_df["season_name"].unique()), index=None,
                              placeholder="Select Season")

st.header(team)

col1, col2, col3, col4 = st.columns(4)

col1.metric("League Position", "2nd")
col2.metric("Points", 68)
col3.metric("Goals For", 65)
col4.metric("Goals Against", 42)

st.divider()



left, right = st.columns(2)

with left:
    st.subheader("Attack")
    attack = pd.DataFrame({
        "Metric": [
            "Goals For",
            "xG",
            "Shots",
            "Big Chances",
            "Conversion %"
        ],
        "Value": [65, 61.4, 485, 91, "14.2%"]
    })

    st.dataframe(attack, width="stretch")

with right:
    st.subheader("Defense")
    defense = pd.DataFrame({
        "Metric": [
            "Goals Against",
            "xGA",
            "Clean Sheets",
            "Tackles",
            "Interceptions"
        ],
        "Value": [42, 30.4, 11, 296, 498]
    })

    st.dataframe(defense, width="stretch")

st.divider()
st.subheader("Recent Results")

fixtures = pd.DataFrame({
    "Opponent": [
        "Liverpool",
        "Chelsea",
        "Spurs",
        "Brighton",
        "Aston Villa"
    ],
    "Result": ["W", "D", "W", "L", "W"],
    "Score": ["2-1", "1-1", "3-0", "0-1", "4-2"]
})

st.dataframe(fixtures, width="stretch")

st.divider()

st.subheader("Squad Statstics")

squad = pd.DataFrame({
    "Player": [
        "<NAME>",
        "<NAME>",
        "<NAME>",
        "<NAME>",
        "<NAME>"
    ],
    "Goals": [18, 12, 7, 5, 3],
    "Assists": [6, 9, 11, 2, 1],
    "Rating": [7.8, 7.5, 7.3, 7.1, 6.9]
})

st.dataframe(squad, width="stretch")