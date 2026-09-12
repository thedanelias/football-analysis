import streamlit as st
import pandas as pd

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)
