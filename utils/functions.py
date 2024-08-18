
import requests
from bs4 import BeautifulSoup
import csv
import os
import pandas as pd
import numpy as np

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Draft():
    def __init__(self, num_players, data, positions):
        self.players = num_players
        self.data = data
        self.positions = positions

class Team():
    def __init__(self, order):
        self.order = order
        self.roster = []

    def pick(self, player, df):
        self.roster.append(player)
        self.data = df[df.Player.isin(self.roster)].copy()


def load_players():
    df = pd.DataFrame()
    for position in ["QB", "RB", "WR", "TE", "K", "DST"]:
        position_df = pd.read_csv(repo_dir + f"/utils/data/FantasyPros_Fantasy_Football_Projections_{position}.csv")
        position_df["position"] = position
        if pd.isna(position_df.iloc[0,2]):
            position_df = position_df.iloc[1:].copy()
        position_df["type"] = None
        position_df.loc[position_df.Player.isna(), "type"] = position_df.loc[position_df.Player.isna(), "Team"]
        position_df.type = position_df.type.fillna("projection")
        position_df.loc[position_df.Team.isin(["high", "low"]), "Team"] = None
        if position == "DST":
            position_df.loc[~position_df.Player.isna(), "Player"] = position_df.loc[~position_df.Player.isna(), "Player"].apply(lambda x: x.split("high")[0])
        else:
            position_df.loc[~position_df.Team.isna(), "Team"] = position_df.loc[~position_df.Team.isna(), "Team"].apply(lambda x: x.split("high")[0])
        position_df.Player = position_df.Player.fillna(method = "ffill")
        position_df.Team = position_df.Team.fillna(method = "ffill")
        df = pd.concat([df, position_df])
    df = df.loc[~df.FPTS.isna(), ["Player", "Team", "FPTS", "position", "type"]]
    df = df.pivot(index = ["Player", "Team", "position"], columns = "type", values = "FPTS").reset_index()
    df["picked"] = 0
    df.sort_values("projection", ascending = True, inplace = True)
    return df[["Player", "Team", "position", "low", "projection", "high", "picked"]]

def create_newpage(position):
    code = f"""
import streamlit as st
from utils.functions import *
st.dataframe(st.session_state.position)
"""
    with open(repo_dir + f"/pages/{position}.py", 'w') as file:
        file.write(code)

