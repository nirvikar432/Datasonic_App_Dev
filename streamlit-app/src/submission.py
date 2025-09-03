import streamlit as st
from policy_tabs import policy_tab
from claims_tabs import claims_tab
from auto_loader import clear_session_state


def submission_tab():

    st.header("View Policies and Claims") 
    st.markdown("<br>", unsafe_allow_html=True)

    
    # Create two columns for the buttons
    col1,col2 = st.columns(2)
    
    # Add description boxes above each button
    with col1:
        st.markdown("""
        <div style="border: 1px solid #ccc; border-radius: 30px; padding: 10px; margin-bottom: 10px; background-color: #144074; height: 120px;">
            <h4 style="color: #23E4BA;">Policy Overview</h4>
            <p>View and track policy details, premiums, and renewal dates.</p>
        </div>
        """, unsafe_allow_html=True)
        policy_button = st.button("Policy", key="policy_button", use_container_width=True, type="primary")
    
    with col2:
        st.markdown("""
        <div style="border: 1px solid #ccc; border-radius: 30px; padding: 10px; margin-bottom: 10px; background-color: #144074; height: 120px;">
            <h4 style="color: #23E4BA;">Claims Overview</h4>
            <p>Monitor claim status, payments, and settlement progress.</p>
        </div>
        """, unsafe_allow_html=True)
        claims_button = st.button("Claims", key="claims_button", use_container_width=True, type="primary")

    # Initialize the view state if not already set
    if "submission_view" not in st.session_state:
        st.session_state.submission_view = None
    
    # Handle button clicks
    if policy_button:
        st.session_state.submission_view = "policy"
        st.rerun()
    
    if claims_button:
        st.session_state.submission_view = "claims"
        st.rerun()
    
    # Display the selected view
    if st.session_state.submission_view == "policy":
        policy_tab()
        # Back button for policy view
        if st.button("Back", key="back_from_policy", type="secondary"):
            st.session_state.submission_view = None
            st.rerun()
            
    elif st.session_state.submission_view == "claims":
        claims_tab()
        # Back button for claims view
        if st.button("Back", key="back_from_claims", type="secondary"):
            st.session_state.submission_view = None
            st.rerun()