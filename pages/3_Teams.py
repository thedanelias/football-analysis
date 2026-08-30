import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title = "Team Analysis",
    layout = "wide"
)

st.title("Team Analysis")

st.sidebar.header("Filters")

team = st.sidebar.selectbox(
    "Select Team",
    ["Manchester City", "Liverpool", "Arsenal"]
)

season = st.sidebar.selectbox(
    "Season",
    ["2025/26", "2024/25"]
)

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