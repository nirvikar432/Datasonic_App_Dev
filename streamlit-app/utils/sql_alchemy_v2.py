from sqlalchemy import create_engine
import pyodbc
import dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus
import streamlit as st

# ✅ Correct LangChain imports for v0.2+
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

# --------------- Streamlit UI ---------------
def chatbotAi():
    st.set_page_config(layout="wide")
    st.header("Datasonic Lakehouse Copilot")

    # Session state (add a messages list to keep chat history)
    if "question" not in st.session_state:
        st.session_state.question = ""
    if "response" not in st.session_state:
        st.session_state.response = None
    if "logic" not in st.session_state:
        st.session_state.logic = ""
    if "messages" not in st.session_state:
        # Each item: {"role": "user" | "assistant", "content": str}
        st.session_state.messages = []

    # --------------- Environment ---------------
    # load_dotenv()
    dotenv.load_dotenv(Path(__file__).parent.parent / ".env")


    SERVER = os.getenv("SERVER")
    DATABASE = os.getenv("DATABASE")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")
    API_KEY = os.getenv("API_KEY")

    # --------------- SQLAlchemy Engine ---------------
    conn = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        "Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={CLIENT_ID};"
        f"PWD={CLIENT_SECRET};"
        f"Authority Id={TENANT_ID};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    engine = create_engine("mssql+pyodbc:///?odbc_connect=" + quote_plus(conn))

    # --------------- LLM + SQL Agent ---------------
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=API_KEY)

    db = SQLDatabase(engine)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    # --------------- Render existing chat history ---------------
    has_chat_api = hasattr(st, "chat_message")  # fallback for older Streamlit versions
    for msg in st.session_state.messages:
        if has_chat_api:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        else:
            who = "You" if msg["role"] == "user" else "AI"
            st.markdown(f"**{who}:** {msg['content']}")

    # --------------- Input + Invoke ---------------
    st.session_state.question = st.text_input("Enter your query")

    if st.button("Ask AI") and st.session_state.question.strip():
        # Add user turn
        st.session_state.messages.append({"role": "user", "content": st.session_state.question})

        # Run agent safely
        try:
            result = agent.invoke({"input": st.session_state.question})
            st.session_state.response = result
            output_text = result["output"] if isinstance(result, dict) and "output" in result else str(result)
        except Exception as e:
            output_text = f"⚠️ Error running agent: {e}"
            st.session_state.response = {"output": output_text}

        # Add assistant turn
        st.session_state.messages.append({"role": "assistant", "content": output_text})

        # Show latest reply immediately
        if has_chat_api:
            with st.chat_message("assistant"):
                st.markdown(output_text)
        else:
            st.markdown(f"**AI:** {output_text}")

    # (Optional) Show intermediate steps for debugging
    if isinstance(st.session_state.response, dict) and "intermediate_steps" in st.session_state.response:
        with st.expander("Intermediate steps"):
            st.write(st.session_state.response["intermediate_steps"])
