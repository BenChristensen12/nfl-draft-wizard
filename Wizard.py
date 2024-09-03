import streamlit as st
from utils.functions import *

if "data" not in st.session_state:
    st.session_state["data"] = load_players()
    st.session_state["roster"] = dict()
    st.session_state["draft_begun"] = False
    st.session_state["rounds"] = 16
    st.session_state["all_picks"] = []
    st.session_state["pick_number"] = 0
    st.session_state["denominators"] = {"QB": 4, "RB": 2, "WR": 2, "TE": 4, "FLEX": 1.5, "K": 8, "DST": 8}

def calculate_lead(pick_num, score = "projection"):
    data = st.session_state.data.sort_values([score], ascending = False)   
    team = st.session_state.draft_order[pick_num]
    roster = st.session_state[f"team_{team}_likely_roster"]
    df = pd.DataFrame()
    for position in roster.keys():
        denominator = st.session_state.denominators[position]
        window = max(round(st.session_state.picks_between[pick_num]/denominator), 1)
        position_df = data[(data.position == position) & (data.picked == 0)].copy()
        position_df["lead"] = position_df[score] - position_df[score].shift(-window)
        df = pd.concat([df, position_df])
    return df

def begin_draft():
    for i in range(st.session_state.num_players):
        st.session_state[f"team_{i+1}_roster"] = dict(zip(st.session_state.roster.keys(), [[] for key in st.session_state.roster.keys()]))
        st.session_state[f"team_{i+1}_likely_roster"] = dict(zip(st.session_state.roster.keys(), [[] for key in st.session_state.roster.keys()]))
        st.session_state[f"team_{i+1}_picks"] = []
        st.session_state[f"team_{i+1}_likely_picks"] = []
    num_players = st.session_state.num_players
    st.session_state["draft_order"] = int(st.session_state.rounds/2) * ([i for i in range(1, num_players+1)] + [i for i in range(num_players, 0, -1)])
    st.session_state["picks_between"] = st.session_state.rounds * [2*(num_players-i) if i < num_players else 2*(num_players-1) for i in range(1, num_players+1)]       
    st.session_state["draft_begun"] = True

def enact_pick():
    team = st.session_state.draft_order[st.session_state.pick_number]
    player, position = st.session_state.pick.Player.values[0], st.session_state.pick.position.values[0]
    st.session_state[f"team_{team}_roster"][position].append(player)
    st.session_state[f"team_{team}_picks"].append(player)
    st.session_state.all_picks.append(player)
    st.session_state.data.loc[st.session_state.data.Player == player, "picked"] = 1
    st.session_state.pick_number += 1


st.title("NFL Draft Wizard")
if not st.session_state.draft_begun:
    num_players = st.number_input("How many teams in your draft?", min_value = 1)
    for i in range(num_players):
        st.session_state[f"team_{i+1}_name"] = st.text_input(f"Team {i + 1} Name:")
    your_num = st.number_input("What number are you?", min_value = 1)
    st.session_state["num_players"] = num_players
    st.session_state["your_num"] = your_num 
    position_choices = st.multiselect("What positions are on the roster?", options = ["QB", "RB", "WR", "TE", "FLEX", "K", "DST"])
    for choice in position_choices:
        position_number = st.number_input(choice, min_value = 1)
        st.session_state.roster[choice] = position_number
    st.button("Enter Draft!", on_click = begin_draft)

else:
    team = st.session_state.draft_order[st.session_state.pick_number]
    if st.session_state.pick_number+1 == st.session_state.your_num:
        st.header("Your pick!")
    else:
        st.header(f"Team {st.session_state[f'team_{team}_name']} is up")
    score = st.selectbox("Select Score to Optimize", options = ["low", "projection", "high"], index = 1)
    tabs = st.tabs(["Recommendation", "QB", "RB", 'WR', 'TE', 'FLEX', 'K', 'D/ST'])
    with tabs[0]:
        st.subheader("Recommended Pick")
        df = calculate_lead(st.session_state.pick_number, score)
        agg_dict ={"Player": "first", "lead": "first", score: "first"}
        highest_lead = df.groupby("position", as_index = False).agg(agg_dict).sort_values("lead", ascending = False)
        highest_pts = df.groupby("position", as_index = False).agg(agg_dict).sort_values([score], ascending = False)
        # df["Rank"] = df.groupby("position")[score].rank(method = 'dense', ascending = False)
        # df.sort_values(["Rank"], inplace = True, ascending = True)
        highest_lead = highest_lead[["position", "Player", score, "lead"]].round().copy()
        highest_lead.insert(0, "Pick", False)
        edited_df = st.data_editor(highest_lead, disabled = ["position", "Player", score, "lead"], hide_index = True)
        if edited_df.Pick.sum() > 0:
            st.session_state.pick = edited_df.loc[edited_df.Pick, ["Player", "position"]]
    positions = ["QB", "RB", 'WR', 'TE', 'FLEX', 'K', 'DST']            
    for i, tab in enumerate(tabs[1:]):
        with tab:
            position = positions[i]
            position_df = df.loc[df.position == position, ["Player", "low", "projection", "high", "lead"]].sort_values(score, ascending = False).round()
            position_df.insert(0, "Pick", False)
            edited_df = st.data_editor(position_df, disabled = ["Player", "low", "projection", "high", "lead"], hide_index = True)
            if edited_df.Pick.sum() > 0:
                st.session_state.pick = df.loc[df.Player == edited_df.loc[edited_df.Pick, "Player"].values[0], ["Player", "position"]]
    st.button("Enact Pick!", on_click = enact_pick)
    st.header("Your Team")
    st.write(st.session_state[f"team_{st.session_state.your_num}_roster"])





    
