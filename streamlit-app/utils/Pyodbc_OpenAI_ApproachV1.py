import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import json 

# from schema_tools import generate_schema, save_schema_artifacts


# --- robust import of local schema_extractor.py -----------------------------
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema_extractor.py")
spec = importlib.util.spec_from_file_location("schema_extractor", SCHEMA_PATH)
schema_extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema_extractor)

# sanity prints (run once; then remove if you like)
print("USING MODULE:", schema_extractor.__file__)
print("HAS generate_schema?", hasattr(schema_extractor, "generate_schema"))
print("HAS save_schema_artifacts?", hasattr(schema_extractor, "save_schema_artifacts"))

# convenient aliases
generate_schema = schema_extractor.generate_schema
save_schema_artifacts = schema_extractor.save_schema_artifacts

# Load environment variables from .env (optional)
load_dotenv()

if "user_query" not in st.session_state: 
   st.session_state.user_query = ""

if "user_query_with_schema" not in st.session_state: 
   st.session_state.user_query_with_schema = ""

if "schema_model" not in st.session_state: 
    st.session_state.schema_model = ""

if "schema_json" not in st.session_state:
   st.session_state.schema_json = ""

if "optimized_prompt" not in st.session_state: 
   st.session_state.optimized_prompt = ""

if "sql_query" not in st.session_state: 
   st.session_state.sql_query = ""

if "query_output" not in st.session_state: 
   st.session_state.query_output = ""

if "final_response" not in st.session_state: 
   st.session_state.final_response = ""

# ---- Load system prompts from txt files ----
# with open("Prompt_Optimizer.txt", "r", encoding="utf-8") as f:
#     prompt_optimizer_system_prompt = f.read()

# with open("SQL_Query_Generator.txt", "r", encoding="utf-8") as f:
#     sql_query_system_prompt = f.read()

# with open("Final_Response_Composer.txt", "r", encoding="utf-8") as f:
#     final_response_system_prompt = f.read()


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

def TestConnection(conn_str):
    """Test the database connection by running a simple query."""
    try:
        with pyodbc.connect(conn_str, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test_value;")
            response = cursor.fetchone()  # Get one row
            return f"Connection Successful! Test Value = {response.test_value}"
    except Exception as e:
        return f"Connection Failed! Error: {e}"
    
def execute_query(conn_str, sql_query): 
   try: 
      with pyodbc.connect(conn_str, timeout=90) as conn:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        response = cursor.fetchall()
        return response
   except Exception as e: 
      return f"Error Encountered! Error: {e}"
    
def api_call(system, user):
    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # or "gpt-4o", "gpt-3.5-turbo", etc.
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    )
    return response.choices[0].message.content.strip()

import re

def clean_sql_output(text: str) -> str:
    # Remove common Markdown/code fences
    text = re.sub(r"^\s*```(?:sql)?\s*|\s*```$", "", text, flags=re.IGNORECASE|re.DOTALL).strip()
    text = re.sub(r"^\s*SQL\s*:\s*", "", text, flags=re.IGNORECASE).strip()
    return text


# --- Streamlit UI ---
print(TestConnection(conn_str=conn))

st.set_page_config(layout="wide")
st.title("AI Interaction Layer")

col1, col2 = st.columns(2)
# with col1: 
#   if st.button("SQL Connection", key="1"):
#     st.text(TestConnection(conn_str=conn))
with col1:
  if st.button("Extract Schema", key="extract"):
    with st.spinner("Extracting schema..."):
        model, columns_df, warnings = generate_schema(conn, server=SERVER, database=DATABASE)
        # Save locally each run (optional)
        save_schema_artifacts(model)
        
        st.session_state.schema_model = model
        st.session_state.schema_json = json.dumps(model, indent=2)
        
        st.success("Schema extracted.")

st.session_state.user_query = st.text_area("Enter your prompt:") 

st.session_state.user_query_with_schema = st.session_state.user_query + st.session_state.schema_json

if st.button("Prompt Optimizer", key="2"):
  system_prompt = '''You are PromptOptimizer. Rewrite a raw user query into ONE concise prompt for a downstream LLM
to generate correct, efficient T-SQL for Azure SQL/Fabric. Use ONLY the provided schema_context.
Do not invent tables/columns.

INPUTS:
- user_query: <<<st.session_state.user_query>>>
- schema_context: <<<st.session_state.user_query_with_schema>>>   # tables/columns and optional human descriptions

SCHEMA HINTS (GoldLakehouse):
- Facts: dbo.fact_policy (home/property), dbo.factpc_auto (auto)
- Home/Property dims: dbo.dim_customer, dbo.dim_property, dbo.dim_location, dbo.dim_payment,
  dbo.dim_coverage, dbo.dim_policy_status, dbo.dim_date, dbo.dim_product (+ *_home variants)
- Auto dims: dbo.dimcustomer_auto, dbo.dimpolicy_auto, dbo.dimvehicle_auto, dbo.dimclaims_auto,
  dbo.dimbroker_auto, dbo.dimfacility_auto
- No enforced FK constraints; infer joins using *_key/id naming.

JOIN HEURISTICS (use when missing in schema):
- fact_policy.customer_key    = dim_customer.customer_key
- fact_policy.property_key    = dim_property.property_key
- fact_policy.location_key    = dim_location.location_key
- fact_policy.payment_key     = dim_payment.payment_key
- fact_policy.coverage_key    = dim_coverage.coverage_key
- fact_policy.policy_status_key = dim_policy_status.status_key
- Date: join fact_policy.cover_start (or quote_date) ↔ dim_date.full_date for grains
- Auto factpc_auto joins:
  - cust_id      ↔ dimcustomer_auto.cust_id
  - chassis_no   ↔ dimvehicle_auto.chassis_no  (or regn ↔ dimvehicle_auto.regn)
  - broker_id    ↔ dimbroker_auto.broker_id
  - facility_id  ↔ dimfacility_auto.facility_id
  - claim_no     ↔ dimclaims_auto.claim_no

YOUR TASK:
Rewrite user_query into a SHORT, schema-aware prompt that the next LLM will follow to produce SQL.
Be decisive. If the user query is ambiguous, make minimal, clearly labeled assumptions.

MUST INCLUDE (in natural, compact prose or bullet list):
1) Line of business: home | auto | mixed | unknown
2) Target output (columns + grain), e.g., “month, policy_count, total_premium”
3) Relevant tables only (subset), with explicit join paths
4) Filters (dates, product/LOB, region/status), mark assumed vs given
5) Measures / aggregations
6) Dialect: “T-SQL for Azure SQL/Fabric”
7) Constraints:
   - Use only listed tables/columns
   - Prefer dim_date for time grouping
   - Avoid SELECT *
   - No full scans beyond necessary joins
   - Add readable aliases

OUTPUT:
Return exactly ONE block starting with:
REFINED_PROMPT:
<the rewritten prompt for the next model to generate SQL>

Do not return JSON. Do not include anything else besides that single block.

EXAMPLES (illustrative):

user_query: “trend of policies and premium by month for last 2 years (home)”
→
REFINED_PROMPT:
Generate T-SQL for Azure SQL/Fabric to return monthly metrics for Home line of business over the last 24 months.
Output columns: month_start, policy_count, total_premium.
Use only these tables/columns and joins:
- dbo.fact_policy(fp): policy_number, premium, cover_start, customer_key, policy_status_key
- dbo.dim_date(dd): full_date, month, year
- dbo.dim_product(dp): lob (assume ‘Home’)
Join rules:
- fp.cover_start = dd.full_date
- (If needed to filter Home) join to dp via product context available to facts; otherwise assume Home filter is not required.
Filters:
- dd.full_date >= DATEADD(MONTH, -24, CAST(GETDATE() AS date))  [assumed]
Measures:
- policy_count = COUNT(DISTINCT fp.policy_number)
- total_premium = SUM(fp.premium)  (remove if column not present)
Constraints:
- Use explicit column lists, readable aliases, and monthly grouping via dim_date.'''
  st.session_state.optimized_prompt = api_call(system=system_prompt, user=st.session_state.user_query_with_schema)

# st.text(st.session_state.user_query + st.session_state.schema_json)
st.text(st.session_state.optimized_prompt)

if st.button("SQL Query Generation", key="3"):
   system_prompt = '''You are an expert in writing efficient, production-safe T-SQL for Azure SQL Database and Microsoft Fabric Lakehouse SQL endpoints.

CONTEXT:
- You will receive ONE refined, schema-aware prompt that lists user intent, required columns, grain, allowed tables, and explicit join paths derived from the Lakehouse schema (dbo.*). 
- Assume execution via pyodbc with a single-statement batch. The output must run as-is.

TASK:
Return EXACTLY ONE SQL SELECT statement that answers the refined prompt.

HARD RULES (STRICT):
1) Output ONLY the SQL query. No comments, explanations, PRINTs, or additional statements. No GO.
2) Do NOT use Markdown, code fences, or backticks of any kind. Output must be raw SQL only.
3) Read-only: SELECT (with CTEs allowed). No DDL/DML, temp tables, table variables, dynamic SQL, or session settings.
4) Use ONLY the tables/columns listed in the refined prompt (Lakehouse schema). Do NOT invent names. Fully qualify as dbo.Table and alias every table.
5) No SELECT *; project explicit columns with readable aliases.
6) Join exactly as specified by the refined prompt. Use ANSI JOINs with ON conditions on indexed/Key columns when given.
7) Use dim_date for time grouping when dates are involved; group by month/year using columns provided (e.g., dd.full_date, dd.calendar_month_start).
8) Null/Type safety:
   - Use COALESCE/ISNULL for nullable measures when aggregating.
   - Use TRY_CAST/TRY_CONVERT for type conversions.
   - Prevent divide-by-zero: denom = NULLIF(denom, 0).
   - For SUM on money/decimal-like fields: CAST to DECIMAL(38, 6) before SUM if necessary.
9) GROUP BY all non-aggregated select columns. Never mix windowed aggregates with grouped aggregates unless required and valid.
10) Filters:
    - Apply ONLY filters stated in the refined prompt (marking any assumptions already handled by the refiner).
    - Use date filters on dim_date when grouping by time; avoid GETDATE() unless explicitly requested, otherwise rely on provided date bounds.
11) Performance hygiene:
    - Project only needed columns.
    - Avoid redundant joins and nested subqueries when a single pass suffices.
    - Prefer CTEs over deeply nested subqueries for readability (but still a single SELECT batch).
12) Deterministic output:
    - If the refined prompt requests “top N” or sample rows, use ORDER BY + OFFSET/FETCH or TOP with an ORDER BY that matches the requested sort.
13) Fabric/Azure SQL compatibility:
    - T-SQL syntax must be valid on Azure SQL / Fabric SQL endpoint.
    - No unsupported hints or server-level features.

OUTPUT FORMAT:
- Return only the final SQL SELECT statement (with optional CTEs). Nothing else.
- The output must be plain text SQL only. Do not include Markdown, ``` fences, ```sql tags, or any prose around it.
- The first non-whitespace character must be "S" (for SELECT) or "W" (for WITH).
- End the statement with a semicolon.
'''
   user_prompt = '''INPUTS:
- schema_context: <<<{st.session_state.user_query_with_schema}>>>   # tables/columns and optional human descriptions'''
   st.session_state.sql_query = api_call(system=system_prompt,user=user_prompt)

st.text(st.session_state.sql_query)

if st.button("Execute Query", key = "4"): 
    st.session_state.query_output = execute_query(conn_str=conn, sql_query=st.session_state.sql_query)

st.text(st.session_state.query_output)


if st.button("Final Response", key="5"): 
    user_prompt = f"""
USER_QUERY:
<<<{st.session_state.user_query}>>>

LAKEHOUSE_SCHEMA_JSON:
<<<{st.session_state.schema_json}>>>

REFINED_PROMPT (intent, grain, filters, measures):
<<<{st.session_state.optimized_prompt}>>>

SQL_QUERY (for reference only; never show verbatim):
<<<{st.session_state.sql_query}>>>

RESULTSET_JSON (array of row objects exactly as returned by the DB):
<<<{st.session_state.query_output}>>>
"""
    system_prompt = '''You are Data Answer Composer. Turn a SQL query’s result set into a concise, correct, user-facing answer.

Inputs (delimited)

USER_QUERY:
<<<st.session_state.user_query>>>

LAKEHOUSE_SCHEMA_JSON:
<<<st.session_state.schema_json>>>

REFINED_PROMPT (intent, grain, filters, measures):
<<<st.session_state.optimized_prompt>>>

SQL_QUERY (for reference only; never show verbatim):
<<<st.session_state.sql_query>>>

RESULTSET_JSON (array of row objects exactly as returned by the DB):
<<<st.session_state.query_output>>>

Rules

1. Use RESULTSET_JSON as the **primary source of truth**. You may reference LAKEHOUSE_SCHEMA_JSON and REFINED_PROMPT only to clarify column meaning, joins, or business context, but **never display schema or SQL to the user**.
2. Do not invent values, tables, or dates. Stay strictly within RESULTSET_JSON.
3. If RESULTSET_JSON is empty → return a short “no data” message and suggest a sensible next step (e.g., broaden dates/filters).
4. Keep answers short first: 1–3 sentences summary, then (if helpful) a compact table.
5. Tables:
   - Show at most 10 rows × 8 columns; if truncated, end with “… and N more rows”.
   - Preserve column names; apply friendly casing/spaces (e.g., policy_count → “Policy count”).
6. Numbers & dates:
   - Add thousands separators; 2–4 decimals for rates/averages; show percentages when a column clearly represents a rate (0–1 or ends with _pct).
   - Render dates as YYYY-MM for monthly grain, YYYY-MM-DD otherwise.
7. If the refined prompt implies totals or comparisons and the result has the needed fields, you may compute lightweight derived text (e.g., sum, min/max, growth vs previous row) but only from RESULTSET_JSON.
8. Explain filters/assumptions briefly (from REFINED_PROMPT) using plain language (e.g., “Home line, last 24 months”).
9. Never expose SQL, schema JSON, internal table names, or join logic to the user. Only surface business-friendly insights.
10. Tone: clear, neutral, business-friendly. No apologies unless an error/no-data case.
11. Output Markdown only. No JSON.

Output format (strict)

- Start with a 1–2 sentence answer summary.
- Optional: a small Markdown table if it materially helps.
- End with a short “Next steps” line with 1–2 suggested follow-ups (optional).'''
    # system_prompt = final_response_system_prompt, user_prompt = user_prompt

    st.session_state.final_response = api_call(system=system_prompt,user=user_prompt)

st.text(st.session_state.final_response)
