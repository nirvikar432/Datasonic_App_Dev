import streamlit as st
import pandas as pd
import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from policy_tabs import policy_tab
from claims_tabs import claims_tab
from submission import submission_tab
from edit_tabs import new_submission_tab
from charts_tab import charts_tab
from toba import toba_tab


# --- Custom Theme ---
# from theme import set_custom_theme

# set_custom_theme()



st.markdown("""
    <style>
            
        .block-container {
            padding-top: 0rem;
        }
        header {visibility: hidden;}
            padding-bottom: 0rem;
        }
        header {visibility: hidden;}
            

         /* Smaller headings */
        h1 {font-size: 1.5rem !important;}
        h2 {font-size: 1.3rem !important;}
        h3 {font-size: 1.2rem !important;}
        h4, h5, h6 {font-size: 1rem !important;}
        p {font-size: 0.8rem !important;}
            

        

        
        
        /* Reduce spacing between elements like tabs, heading,table */
        .element-container {
            margin-bottom: -10px !important;
        }
        

        
        /* Reduce spacing between title and content */
        h1, h2, h3 {
            margin-bottom: 0rem !important;
            margin-top: 0rem !important;

        }
        
        /* Reduce tab content padding */
        .stTabs > div > div > div > div {
            padding-top: 0rem;
        }
        
        /* Reduce spacing between form elements */
        .stForm {
            margin-bottom: 0px;
        }
        
        /* Add space between tab buttons Policies Claims etc.*/
        .stTabs [data-baseweb="tab-list"] button {
            margin-right: 20px !important;
        }
            
        /* Add fade-in animation for the main container */
        .block-container {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }

    </style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Datasonic",
    page_icon=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'AdroDatasonic.png')),
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)

def main():
    import streamlit as st
    import base64

    LOGO_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'AdroDatasonic.png'))

    st.markdown(
        """
        <style>
        .container {
            display: flex;
        }
        .logo-text {
            font-weight:700 !important;
            font-size:45px !important;
            color: #FF7601 !important;
            padding-top: 10px !important;
        }
        .logo-img {
            float:right;
            width: 100px !important;
            height: 100px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="container">
            <img class="logo-img" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
            <p class="logo-text">Policy and Claims Management</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    #add an icon with the text "Datasonic" in the top left corner
    # st.title("Policy and Claims Management")
    tabs = st.tabs(["View", "New Submission", "TOBA On-boarding", "Analytics"])

    with tabs[0]:
        submission_tab()
    with tabs[1]:
        new_submission_tab()
    with tabs[2]:
        toba_tab()
    with tabs[3]:
        charts_tab()


if __name__ == "__main__":
    main()