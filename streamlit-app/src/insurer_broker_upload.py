from time import time
import streamlit as st
import json
import sys
import os
from datetime import datetime, date
import time
import random

# Use absolute import for testing
from broker_form import broker_form
from insurer_form import insurer_form


from db_utils import fetch_data, insert_claim, insert_broker, insert_insurer


# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fetch json data from json.json file
def fetch_json_data():
    """Fetch JSON data from a file"""
    try:
        #For Testing purposes, we can use a static file path
        json_files = [
            "streamlit-app/utils/json/TOBA_Broker.json",
            "streamlit-app/utils/json/TOBA_Insurer.json"
        ]
        selected_file = random.choice(json_files)

        # with open("streamlit-app/utils/json/TOBA_Insurer.json", "r") as f:
        with open(selected_file, "r") as f:
            data = json.load(f)
            st.write("JSON Data Loaded:", data)
        return data
    except Exception as e:
        st.error(f"Error loading JSON data: {e}")
        return None

def load_data_from_json():
    """Load policy data from JSON and route to appropriate form"""
    try:
        data = fetch_json_data()
        if not data:
            return False
        
        policy_type = data.get("Type", "")
        if policy_type == "Broker":
            st.session_state.form_to_show = "broker_manual_form"
            st.session_state.form_defaults = data
            return True
        elif policy_type == "Insurer":
            st.session_state.form_to_show = "insurer_manual_form"
            st.session_state.form_defaults = data
            return True
        else:
            st.error(f"Unknown TOBA type: {policy_type}")
            return False
    except Exception as e:
        st.error(f"Error loading TOBA data: {e}")
        return False

def show_insurer_broker_form():

    if hasattr(st.session_state, "form_to_show") and st.session_state.form_to_show:
        defaults = st.session_state.get("form_defaults", {})

        if st.session_state.form_to_show == "broker_manual_form":
            form_data, submit, back = broker_form(defaults)

            if submit:
                try:
                    insert_broker(form_data)
                    # st.session_state.broker_data = form_data
                    st.session_state.toba_page = "main"  # Go to main page after submit
                    if "form_to_show" in st.session_state:
                        del st.session_state.form_to_show
                    if "form_defaults" in st.session_state:
                        del st.session_state.form_defaults
                    st.success("Broker added successfully!")
                    time.sleep(5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add broker: {e}")
            if back:
                st.session_state.toba_page = "main"
                st.session_state.show_broker_summary = False
                st.rerun()

        if st.session_state.form_to_show == "insurer_manual_form":
            form_data, submit, back = insurer_form(defaults)

            if submit:
                try:
                    insert_insurer(form_data)
                    st.session_state.toba_page = "main"  # Go to main page after submit
                    if "form_to_show" in st.session_state:
                        del st.session_state.form_to_show
                    if "form_defaults" in st.session_state:
                        del st.session_state.form_defaults
                    st.success("Insurer added successfully!")
                    time.sleep(5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add insurer: {e}")
            if back:
                st.session_state.toba_page = "main"
                st.rerun()

    

