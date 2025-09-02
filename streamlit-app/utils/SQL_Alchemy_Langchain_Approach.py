from sqlalchemy import create_engine
import pyodbc
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
import streamlit as st


# ✅ Correct LangChain imports for v0.2+
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

if "question" not in st.session_state: 
    st.session_state.question = ""

if "response" not in st.session_state: 
    st.session_state.response = ""

if "logic" not in st.session_state: 
    st.session_state.logic = ""

load_dotenv()

# Environment Variables
SERVER = os.getenv("SERVER")
DATABASE = os.getenv("DATABASE")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
API_KEY = os.getenv("API_KEY")
TENANT_ID = os.getenv("TENANT_ID")
API_KEY = os.getenv("API_KEY")

# Build connection string
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

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=API_KEY)

# ---------- LangChain SQL agent ----------
db = SQLDatabase(engine)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True, handle_parsing_errors=True, return_intermediate_steps = True)



#---------------Streamlit start-------------------------# 
st.set_page_config(layout="wide")
st.header("Datasonic Lakehouse Copilot")

st.session_state.question = st.text_input("Enter your query")
if st.button("Ask AI"):
    st.session_state.response = agent.invoke({"input": st.session_state.question})
    st.subheader("Answer")


st.text(st.session_state.response['output'])
