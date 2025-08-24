import os
import pandas as pd
import numpy as np
import requests, json
import streamlit as st

def initialize_dashboard():
    st.session_state["data"] = retrieve_espn_api()
    st.session_state.data["Taken"] = False
    st.session_state.data["at_risk"] = False
    st.session_state["position_counts"] = dict()
    st.session_state["positions"] = ["QB", "RB", "WR", "TE", "Flex", "K", "DST"]
    st.session_state["draft_begun"] = False
    st.session_state["all_picks"] = []
    st.session_state["pick_number"] = 0
    st.session_state["denominators"] = {"QB": 4, "RB": 2, "WR": 2, "TE": 4, "K": 8, "DST": 8}
    st.session_state["round"] = 1    

def prompt_draft_details():
    st.session_state["num_players"] = st.number_input("How many teams in your draft?", min_value = 2)
    st.session_state["your_num"] = st.number_input("What number are you in the draft?", min_value = 1)

    chosen_positions = st.multiselect("What positions are on the roster?", options = st.session_state.positions)
    st.session_state["chosen_positions"] = chosen_positions
    if chosen_positions:
        for position in chosen_positions:
            position_count = st.number_input(f"How many {position}?", min_value = 1)
            st.session_state.position_counts[position] = position_count
        bench_count = st.number_input("How many on the bench?", min_value = 1)
        st.session_state["bench_count"] = bench_count
    st.button("Enter Draft!", on_click = begin_draft)    

def begin_draft():
    roster = pd.DataFrame(columns = ["Position", "Player", "Projection", "Average Draft Position", "Your Draft Position", "Season Outlook"])
    st.session_state.data = st.session_state.data[st.session_state.data.position.isin(list(set(st.session_state.chosen_positions) | set(["TE"])))]
    for position in st.session_state.chosen_positions:
        for i in range(st.session_state.position_counts[position]):
            roster.loc[len(roster)] = [position, None, None, None, None, None]
    for i in range(st.session_state.bench_count):
        roster.loc[len(roster)] = ["Bench", None, None, None, None, None]
    st.session_state["roster"] = roster.copy()
    st.session_state["rounds"] = len(roster)
    y, n = st.session_state.your_num, st.session_state.num_players
    repeats = int(st.session_state.rounds / 2)
    st.session_state["draft_order"] = repeats * ([i for i in range(1, n+1)] + [i for i in range(n, 0, -1)])
    st.session_state["your_pick_order"] = sorted([2*k*n + y for k in range(repeats)] + [2*k*n + 2*n + 1-y for k in range(repeats)])
    st.session_state["picks_between"] = st.session_state.rounds * [2*(n-i) if i < n else 2*(n-1) for i in range(1, n+1)]
    
    st.session_state["draft_begun"] = True

def update_roster_with_roster_df(row, pick_number):
    position = row["position"]
    roster_position_df = st.session_state.roster[st.session_state.roster.Player.isna() & (st.session_state.roster.Position == position)].copy()
    if len(roster_position_df) > 0:
        st.session_state.roster.loc[roster_position_df.index[0]] = [row["position"], row["Player"], row["projection"], row["draft_position"], pick_number+1, row["outlook"]]
    elif position in ["RB", "WR", "TE"]:
        roster_position_df = st.session_state.roster[st.session_state.roster.Player.isna() & (st.session_state.roster.Position == "Flex")].copy()
        if len(roster_position_df) > 0:
            st.session_state.roster.loc[roster_position_df.index[0]] = ["Flex", row["Player"], row["projection"], row["draft_position"], pick_number+1, row["outlook"]]
        else:
            roster_position_df = st.session_state.roster[st.session_state.roster.Player.isna() & (st.session_state.roster.Position == "Bench")].copy()
            st.session_state.roster.loc[roster_position_df.index[0]] = ["Bench", row["Player"], row["projection"], row["draft_position"], pick_number+1, row["outlook"]]
    else:
        roster_position_df = st.session_state.roster[st.session_state.roster.Player.isna() & (st.session_state.roster.Position == "Bench")].copy()
        st.session_state.roster.loc[roster_position_df.index[0]] = ["Bench", row["Player"], row["projection"], row["draft_position"], pick_number+1, row["outlook"]]

def fetch_all_players():
    url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leaguedefaults/3?view=kona_player_info"
    all_players = []
    offset = 0
    page_size = 200  # safe chunk; bump if you like
    while True:
        xff = {
            "players": {
                "limit": page_size,
                "offset": offset,
                "sortPercOwned": {"sortPriority": 1, "sortAsc": False}
            }
        }
        headers = {
            "Accept": "application/json",
            "X-Fantasy-Filter": json.dumps(xff),
        }
        r = requests.get(url, headers=headers)#, verify=False)
        r.raise_for_status()
        page = r.json().get("players", [])
        if not page:
            break
        all_players.extend(page)
        offset += len(page)
        return all_players

def retrieve_espn_api():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    config = json.load(open(repo_dir + "/config.json"))    
    players = fetch_all_players()
    names, positions, draft_positions, outlooks, projections = [], [], [], [], []
    for player_dict in players:
        names.append(player_dict['player']['fullName'])
        positions.append(config["defaultPositionId"][str(player_dict['player']['defaultPositionId'])])
        draft_positions.append(player_dict['player']['ownership']['averageDraftPosition'])
        if 'seasonOutlook' in player_dict['player'].keys():
            outlook = player_dict['player']['seasonOutlook']
        else: 
            outlook = None
        outlooks.append(outlook)
        for stat_dict in player_dict['player']['stats']:
            if stat_dict['externalId'] == '2025':
                projections.append(stat_dict["appliedTotal"])
                break

    espn_data = pd.DataFrame({"Player": names,
                              "position": positions,
                              "draft_position": draft_positions,
                              "outlook": outlooks,
                              "projection": projections})
    
    return espn_data.sort_values("draft_position", ignore_index = True)






