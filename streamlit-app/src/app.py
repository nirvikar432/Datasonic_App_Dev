import streamlit as st
import pandas as pd
import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from db_utils import fetch_data, insert_policy, update_policy
from policy_forms import policy_manual_form
from policy_status_utils import update_policy_lapsed_status
from policy_tabs import policy_tab
from claims_tabs import claims_tab
from edit_tabs import policy_edit_tab, claims_edit_tab
from charts_tab import charts_tab

# --- Custom Theme ---
# from theme import set_custom_theme

# set_custom_theme()

st.markdown("""
    <style>
        .block-container {
            padding-top: 0rem;
        }
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Datasonic Orbit",
    page_icon=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'datasonic_orbit.ico')),
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)

def main():
    st.title("Policy and Claims Management")
    tabs = st.tabs(["Policies", "Claims", "Policy Edit", "Claims Edit", "Analytics"])

    with tabs[0]:
        policy_tab()
    with tabs[1]:
        claims_tab()
    with tabs[2]:
        policy_edit_tab()
    with tabs[3]:
        claims_edit_tab()
    with tabs[4]:
        charts_tab()

if __name__ == "__main__":
    main()