import pyodbc
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

def fetch_data(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(query)
    data = cursor.fetchall()
    
    # Convert data to a list of dictionaries for easier handling
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in data]
    
    cursor.close()
    conn.close()
    
    return results