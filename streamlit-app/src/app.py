import streamlit as st
import pandas as pd
import sys
import os
import base64

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from policy_tabs import policy_tab
from claims_tabs import claims_tab
from submission import submission_tab
from edit_tabs import new_submission_tab
from charts_tab import charts_tab
from toba import toba_tab
from chatbot import chatbot_interface  # ✅ ADD CHATBOT IMPORT


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
        /* Footer Styles */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: linear-gradient(0deg, rgba(13, 121, 133, 0.88) 0.01%, rgba(26, 44, 71, 0.88) 32.36%, #1A2C47 108.63%);
            color: white;
            text-align: center;
            padding: 1px 0;
            z-index: 999;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            flex-wrap: wrap;
        }
        
        .footer-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .footer-logo {
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }
        
        .footer-text {
            font-size: 14px;
            font-weight: 500;
            margin: 0;
        }
            
        .footer-center {
            display: flex;
            align-items: center;
            gap: 20px;
            margin: 0 20px;
        }
        
        .footer-right {
            font-size: 12px;
            opacity: 0.8;
        }
        
        /* Responsive footer */
        @media (max-width: 768px) {
            .footer-content {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            
            .footer-center {
                margin: 10px 0;
            }
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

def create_footer():
    
    LOGO_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'AdroDatasonic.png'))
    
    footer_html = f"""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-left">
                <img class="footer-logo" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}" alt="Datasonic Logo">
                <div>
                    <p class="footer-text">AdroDatasonic 3.0</p>
                </div>
            </div>
               © 2025 ADROSONIC®
        </div>
    </div>
    """
    
    st.markdown(footer_html, unsafe_allow_html=True)





def main():
    import streamlit as st
    import base64

    LOGO_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'AdroDatasonic.png'))
    ADROSONIC_LOGO_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'media', 'Adrosonic.png'))

    st.markdown(
        """
        <style>
        
        .container {
            display: flex;
        }
        .logo-text {
            font-weight:700 !important;
            font-size:36px !important;
            color: #FFFFFF !important;
            font-family: "Montserrat", sans-serif !important;
            padding-top: 5px !important;
        }
        .logo-img {
            float:right;
            width: 70px !important;
            height: 70px !important;
            margin-right: 0px !important;
            margin-top: 0px !important;
        }
        .logo-img2 {
            float:right;
            width: 250px !important;
            height: 50px !important;
            margin-right: 0px !important;
            margin-top: 0px !important;
        }
        .container-right {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        position: absolute;
        top: 10px;
        right: 20px;
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

        <div class="container-right">
            <img class="logo-img2" src="data:image/png;base64,{base64.b64encode(open(ADROSONIC_LOGO_IMAGE, "rb").read()).decode()}">
        </div>
        """,
        unsafe_allow_html=True
    )
    #add an icon with the text "Datasonic" in the top left corner
    # st.title("Policy and Claims Management")
    # tabs = st.tabs(["View", "New Submission", "TOBA On-boarding", "Analytics"])

    tabs = st.tabs(["View", "New Submission", "TOBA On-boarding", "Chat AI"])

    with tabs[0]:
        submission_tab()
    with tabs[1]:
        new_submission_tab()
    with tabs[2]:
        toba_tab()
    # with tabs[3]:
    #     computer_Vision()
    with tabs[3]:
        # log_viewer_tab()
        chatbot_interface()
    #     charts_tab()

    # Add footer at the bottom
    create_footer()

if __name__ == "__main__":
    main()