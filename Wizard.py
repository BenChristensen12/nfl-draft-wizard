import streamlit as st
from time import time
from utils.functions import *

st.set_page_config(layout="wide")

if "data" not in st.session_state:
    initialize_dashboard()


if not st.session_state.draft_begun:
    st.title("NFL Draft Wizard")
    prompt_draft_details()

else:
    with st.sidebar:
        st.header("Your Picks")
        st.dataframe(st.session_state.roster, hide_index = True)
    pick_number = st.session_state.data.Taken.sum()
    if pick_number+1 in st.session_state.your_pick_order:
        st.markdown(
            "<h1 style='background-color:yellow; color:black; padding:10px; border-radius:10px;'>"
            "⚡ Your Pick!"
            "</h1>",
            unsafe_allow_html=True
        )
    else:
        st.title("NFL Draft Wizard")

    st.subheader("Recommended Pick")
    at_risk_rows = st.session_state.data[~st.session_state.data.Taken].head(st.session_state.picks_between[pick_number]).index
    st.session_state.data.loc[at_risk_rows, "at_risk"] = True
    max_projections = st.session_state.data[~st.session_state.data.Taken].groupby("position").projection.max()
    leads =  max_projections - st.session_state.data[(~st.session_state.data.Taken)& (~st.session_state.data.at_risk)].groupby("position").projection.max()    
    for position in st.session_state.chosen_positions:
        if position != "Flex":
            if st.session_state.data.loc[(~st.session_state.data.Taken) & (st.session_state.data.projection == max_projections[position]), "at_risk"].values[0]:
                st.session_state.data.loc[(~st.session_state.data.Taken) & (st.session_state.data.projection == max_projections[position]), "lead"] = leads[position]
            else:
                st.session_state.data.loc[(~st.session_state.data.Taken) & (st.session_state.data.projection == max_projections[position]), "lead"] = st.session_state.data[(~st.session_state.data.Taken)& (st.session_state.data.position == position)].projection.max() - st.session_state.data[(~st.session_state.data.Taken)& (st.session_state.data.position == position) & (st.session_state.data.projection < max_projections[position])].projection.max()
    agg_dict ={"Player": "first", "lead": "first", "projection": "first", "at_risk": "first"}
    highest_lead = st.session_state.data[(~st.session_state.data.Taken)].sort_values("projection", ascending = False).groupby("position", as_index = False).agg(agg_dict).sort_values(["lead", "projection"], ascending = False)
    highest_lead = highest_lead[["position", "Player", "projection", "lead", "at_risk"]].round().copy()
    st.dataframe(highest_lead.round(), hide_index = True)    
    positions = st.session_state.chosen_positions  
    st.subheader(f"Current Pick: {pick_number+1}")  
    tabs = st.tabs(["All"] + positions)
    picked = set()
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0:
                data_df = st.session_state.data.sort_values(["Taken", "draft_position"])[["Taken", "position", "Player", "projection", "lead", "at_risk"]].round()
            elif positions[i-1] == "Flex":
                data_df = st.session_state.data.loc[st.session_state.data.position.isin(["WR", "RB", "TE"])].round()
                lead = data_df.loc[~data_df.Taken].projection.max() - data_df.loc[(~st.session_state.data.Taken)& (~st.session_state.data.at_risk), "projection"].max()
                data_df["lead"] = None
                data_df.sort_values(["Taken", "projection"], ascending = [True, False], inplace = True)
                data_df.loc[0, "lead"] = lead
                data_df = data_df[["Taken", "Player", "position", "projection", "lead", "at_risk", "outlook"]].copy()
            else:
                position = positions[i-1]
                data_df = st.session_state.data.sort_values(["Taken", "draft_position"]).loc[st.session_state.data.position == position, ["Taken", "Player", "projection", "lead", "at_risk", "outlook"]].round()
                
            edited_df = st.data_editor(data_df, disabled = ["position", "Player", "projection", "lead", "at_risk"], hide_index = True, use_container_width=True)
            picked.update(edited_df.loc[edited_df.Taken, "Player"].values)
    picked = list(picked)
    if len(picked) != st.session_state.data.Taken.sum():
        if pick_number+1 in st.session_state.your_pick_order:
            player_picked = list(set(picked) - set(st.session_state.data.loc[st.session_state.data.Taken, "Player"].values))[0]
            row = st.session_state.data[st.session_state.data.Player == player_picked].iloc[0]
            update_roster_with_roster_df(row, pick_number)
        st.session_state.data.Taken = False
        st.session_state.data.lead = None
        st.session_state.data.loc[st.session_state.data.Player.isin(picked), "Taken"] = True
        st.rerun()

# Allow picking from recommended pick table
# Enforce player limits so you can't pick more than allowed
# Fix end-of-draft index out of range error
