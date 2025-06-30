import streamlit as st

def set_custom_theme():
    st.markdown("""
        <style>
            :root {
                --primary-color: slateBlue;
                --background-color: mintCream;
                --secondary-background-color: darkSeaGreen;
                --base-radius: 999px;
            }
            .stApp {
                background-color: mintCream !important;
            }
            .stButton>button, .stTextInput>div>input, .stSelectbox>div>div>div {
                border-radius: 999px !important;
            }
            .stTabs [data-baseweb="tab-list"] button {
                border-radius: 999px 999px 0 0 !important;
            }
            .stProgress > div > div > div > div {
                background-color: slateBlue !important;
            }
            .stMetric {
                background-color: darkSeaGreen !important;
                border-radius: 999px !important;
                padding-left: 100px;
            }
            .st-cq {
                background-color: darkSeaGreen !important;
                border-radius: 999px !important;
            }
        </style>
    """, unsafe_allow_html=True)