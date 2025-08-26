import pandas as pd
import numpy as np
import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
 

    # Define your connection parameters
    server = 'datasonic.database.windows.net'
    database = 'datasonicdb'
    username = 'nirvikar'
    password = 'datasonic@123'

    # Create a connection string
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # Establish a connection to the database
    conn = pyodbc.connect(connection_string)
    return conn

# Connect to SQL Server using your existing method
conn = get_db_connection()

if conn:
    print("✅ Database connected successfully")
    
    # Load broker table
    df = pd.read_sql("SELECT * FROM [dbo].[broker]", conn)
    print(f"📊 Loaded {len(df)} broker records")
    
    # Convert onboarding date
    df['Date_Of_Onboarding'] = pd.to_datetime(df['Date_Of_Onboarding'])
    
    # Generate Submission_Date
    random_days = np.random.choice([1, 2, 3], size=len(df))
    df['Submission_Date'] = df['Date_Of_Onboarding'] - pd.to_timedelta(random_days, unit='days')
    
    # Push back into SQL
    cursor = conn.cursor()
    for idx, row in df.iterrows():
        cursor.execute("""
            UPDATE [dbo].[broker]
            SET Submission_Date = ?
            WHERE Broker_ID = ?
        """, row['Submission_Date'], row['Broker_ID'])
    
    conn.commit()
    print("✅ Database updated successfully")
    conn.close()
else:
    print("❌ Failed to connect to database")