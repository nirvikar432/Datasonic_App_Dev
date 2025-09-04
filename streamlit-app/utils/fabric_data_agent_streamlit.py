import os
import time
import streamlit as st
from fabric_data_agent_client import FabricDataAgentClient  # reuse your class
import dotenv
from pathlib import Path

# Load env vars
def chatbotAi():
    try:
        dotenv.load_dotenv(Path(__file__).parent.parent / ".env")        
    except ImportError:
        pass

    TENANT_ID = os.getenv("TENANT_ID")
    DATA_AGENT_URL = os.getenv("DATA_AGENT_URL")

    # Streamlit UI
    # st.set_page_config(page_title="Fabric Data Agent", page_icon="🤖")
    # st.title("🤖 Fabric Data Agent Client")

    # if TENANT_ID or DATA_AGENT_URL :
    #     st.error("❌ Please set TENANT_ID and DATA_AGENT_URL in a .env file or environment variables.")
    #     st.stop()

    # Authenticate once per session
    @st.cache_resource
    def init_client():
        return FabricDataAgentClient(
            tenant_id=TENANT_ID,
            data_agent_url=DATA_AGENT_URL
        )

    client = init_client()

    # Input box for user question
    user_query = st.text_area("Enter your query:", placeholder="e.g. Show me the top 5 records from any available table")

    if st.button("Ask Agent"):
        if not user_query.strip():
            st.warning("⚠️ Please enter a query.")
        else:
            with st.spinner("Contacting Fabric Data Agent..."):
                response = client.ask(user_query)
            st.success("✅ Response received!")
            st.markdown("### 💬 Agent Response")
            st.write(response)
