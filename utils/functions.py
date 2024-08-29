
import requests
from bs4 import BeautifulSoup
import csv
import os
import pandas as pd
import numpy as np

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    df.sort_values("projection", ascending = False, inplace = True)
    df["likely_pick"] = 0
    return df[["Player", "Team", "position", "low", "projection", "high", "picked", "likely_pick"]]