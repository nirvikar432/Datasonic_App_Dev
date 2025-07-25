from datetime import time
import pyodbc
import streamlit as st
import time

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

def insert_policy(policy_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = ', '.join(policy_data.keys())
    placeholders = ', '.join(['?'] * len(policy_data))
    sql = f"INSERT INTO Policy ({columns}) VALUES ({placeholders})"
    try:
        cursor.execute(sql, list(policy_data.values()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_policy(policy_no, update_fields):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ', '.join([f"{col} = ?" for col in update_fields.keys()])
    sql = f"UPDATE Policy SET {set_clause} WHERE POLICY_NO = ?"
    params = list(update_fields.values()) + [policy_no]
    cursor.execute(sql, params)
    conn.commit()
    cursor.close()
    conn.close()


def execute_query(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# def insert_quotation(quotation_data):
#     """
#     Insert a new quotation record into the Quotations table
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # Prepare the SQL insert statement
#         insert_query = """
#         INSERT INTO Quotations (
#             TEMP_POLICY_ID, CUST_ID, CUST_NAME, CUST_DOB, CUST_CONTACT, CUST_EMAIL,
#             EXECUTIVE, CHASSIS_NO, MAKE, MODEL, MODEL_YEAR, REGN, USE_OF_VEHICLE,
#             DRV_DOB, DRV_DLI, VEH_SEATS, COVERAGE_TYPE, SUM_INSURED, PREMIUM_ESTIMATE,
#             PRODUCT_TYPE, POLICY_TYPE, VALIDITY_PERIOD, VALIDITY_EXPIRY, STATUS,
#             CREATED_DATE, REMARKS
#         ) VALUES (
#             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
#         )
#         """
        
#         # Prepare the values tuple
#         values = (
#             quotation_data.get("TEMP_POLICY_ID"),
#             quotation_data.get("CUST_ID"),
#             quotation_data.get("CUST_NAME"),
#             quotation_data.get("CUST_DOB"),
#             quotation_data.get("CUST_CONTACT"),
#             quotation_data.get("CUST_EMAIL", ""),  # Optional field
#             quotation_data.get("EXECUTIVE"),
#             quotation_data.get("CHASSIS_NO"),
#             quotation_data.get("MAKE"),
#             quotation_data.get("MODEL"),
#             quotation_data.get("MODEL_YEAR"),
#             quotation_data.get("REGN", ""),  # Optional field
#             quotation_data.get("USE_OF_VEHICLE"),
#             quotation_data.get("DRV_DOB"),
#             quotation_data.get("DRV_DLI"),
#             quotation_data.get("VEH_SEATS"),
#             quotation_data.get("COVERAGE_TYPE"),
#             float(quotation_data.get("SUM_INSURED", 0)),
#             float(quotation_data.get("PREMIUM_ESTIMATE", 0)),
#             quotation_data.get("PRODUCT_TYPE"),
#             quotation_data.get("POLICY_TYPE", ""),  # Optional field
#             quotation_data.get("VALIDITY_PERIOD"),
#             quotation_data.get("VALIDITY_EXPIRY"),
#             quotation_data.get("STATUS", "Draft"),
#             quotation_data.get("CREATED_DATE"),
#             quotation_data.get("REMARKS", "")  # Optional field
#         )
        
#         # Execute the query
#         cursor.execute(insert_query, values)
#         conn.commit()
#         print(f"Quotation {quotation_data.get('TEMP_POLICY_ID')} inserted successfully.")
        
#     except Exception as e:
#         conn.rollback()
#         print(f"Error inserting quotation: {e}")
#         raise e
#     finally:
#         cursor.close()
#         conn.close()


# def update_quotation(temp_policy_id, updates):
#     """
#     Update an existing quotation record
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # Build the SET clause dynamically based on provided updates
#         set_clauses = []
#         values = []
        
#         for key, value in updates.items():
#             set_clauses.append(f"{key} = ?")
#             values.append(value)
        
#         # Add UPDATED_DATE
#         set_clauses.append("UPDATED_DATE = GETDATE()")
        
#         set_clause = ", ".join(set_clauses)
#         values.append(temp_policy_id)  # For WHERE clause
        
#         update_query = f"""
#         UPDATE Quotations 
#         SET {set_clause}
#         WHERE TEMP_POLICY_ID = ?
#         """
        
#         cursor.execute(update_query, values)
#         conn.commit()

#         if cursor.rowcount > 0:
#             print(f"Quotation {temp_policy_id} updated successfully.")
#         else:
#             print(f"No quotation found with TEMP_POLICY_ID: {temp_policy_id}")
            
#     except Exception as e:
#         conn.rollback()
#         print(f"Error updating quotation: {e}")
#         raise e
#     finally:
#         cursor.close()
#         conn.close()


# def fetch_quotation_by_temp_id(temp_policy_id):
#     """
#     Fetch a specific quotation by TEMP_POLICY_ID
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         query = "SELECT * FROM Quotations WHERE TEMP_POLICY_ID = ?"
#         cursor.execute(query, (temp_policy_id,))
        
#         columns = [column[0] for column in cursor.description]
#         result = cursor.fetchone()
        
#         if result:
#             return dict(zip(columns, result))
#         else:
#             return None
            
#     except Exception as e:
#         print(f"Error fetching quotation: {e}")
#         raise e
#     finally:
#         cursor.close()
#         conn.close()


# def fetch_quotation_history(cust_id, limit=10):
#     """
#     Fetch quotation history for a specific customer
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         query = """
#         SELECT TEMP_POLICY_ID, CREATED_DATE, COVERAGE_TYPE, PREMIUM_ESTIMATE, 
#                STATUS, VALIDITY_PERIOD, VALIDITY_EXPIRY, MAKE, MODEL
#         FROM Quotations 
#         WHERE CUST_ID = ? 
#         ORDER BY CREATED_DATE DESC
#         """
        
#         if limit:
#             query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
        
#         cursor.execute(query, (cust_id,))
        
#         columns = [column[0] for column in cursor.description]
#         results = cursor.fetchall()
        
#         return [dict(zip(columns, row)) for row in results]
        
#     except Exception as e:
#         print(f"Error fetching quotation history: {e}")
#         return []
#     finally:
#         cursor.close()
#         conn.close()


# def fetch_all_quotations(status=None, limit=100):
#     """
#     Fetch all quotations with optional status filter
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         base_query = """
#         SELECT TEMP_POLICY_ID, CUST_ID, CUST_NAME, EXECUTIVE, MAKE, MODEL,
#                COVERAGE_TYPE, PREMIUM_ESTIMATE, STATUS, CREATED_DATE, VALIDITY_EXPIRY
#         FROM Quotations
#         """
        
#         if status:
#             query = base_query + " WHERE STATUS = ? ORDER BY CREATED_DATE DESC"
#             if limit:
#                 query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
#             cursor.execute(query, (status,))
#         else:
#             query = base_query + " ORDER BY CREATED_DATE DESC"
#             if limit:
#                 query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
#             cursor.execute(query)
        
#         columns = [column[0] for column in cursor.description]
#         results = cursor.fetchall()
        
#         return [dict(zip(columns, row)) for row in results]
        
#     except Exception as e:
#         print(f"Error fetching quotations: {e}")
#         return []
#     finally:
#         cursor.close()
#         conn.close()


# def mark_quotation_converted(temp_policy_id, policy_no):
#     """
#     Mark a quotation as converted to policy
#     """
#     try:
#         updates = {
#             "STATUS": "Converted",
#             "CONVERTED_TO_POLICY": policy_no
#         }
#         update_quotation(temp_policy_id, updates)
#         print(f"Quotation {temp_policy_id} marked as converted to policy {policy_no}")
        
#     except Exception as e:
#         print(f"Error marking quotation as converted: {e}")
#         raise e
    
def insert_claim(claim_data):
    """Insert new claim into database"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    columns = ', '.join(claim_data.keys())
    placeholders = ', '.join(['?' for _ in claim_data])
    values = tuple(claim_data.values())
    
    query = f"INSERT INTO Claims ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()

def update_claim(claim_no, update_data):
    """Update existing claim in database"""    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
    values = tuple(update_data.values()) + (claim_no,)
    
    query = f"UPDATE Claims SET {set_clause} WHERE CLAIM_NO = ?"
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    




# def insert_broker(broker_data):
#     """Insert broker with error handling"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         insert_query = """
#         INSERT INTO Broker (
#             Broker_ID, Broker_Name, Commission, Date_Of_Onboarding,
#             FCA_Registration_Number, Broker_Type, Market_Access, Delegated_Authority
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """
        
#         values = (
#             broker_data.get("Broker_ID"),
#             broker_data.get("Broker_Name"),
#             broker_data.get("Commission"),
#             broker_data.get("Date_Of_Onboarding"),
#             broker_data.get("FCA_Registration_Number"),
#             broker_data.get("Broker_Type"),
#             broker_data.get("Market_Access"),
#             broker_data.get("Delegated_Authority")
#         )
        
#         cursor.execute(insert_query, values)
#         conn.commit()
        
#     except pyodbc.IntegrityError as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Broker data integrity error: {e}")
#         st.info("💡 This usually means the Broker ID already exists")
#         raise
#     except pyodbc.Error as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Database error during broker insertion: {e}")
#         raise
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Unexpected error during broker insertion: {e}")
#         raise
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()



# # def update_broker(fca_registration, update_fields):
#     """Update broker fields by FCA Registration Number"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
#         values = list(update_fields.values()) + [fca_registration]
#         update_query = f"UPDATE Broker SET {set_clause} WHERE FCA_Registration_Number = ?"
#         cursor.execute(update_query, values)
#         conn.commit()
#         st.success(f"Broker updated for FCA Registration Number {fca_registration}.")

#     except pyodbc.Error as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Database error during broker update: {e}")
#         raise
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Unexpected error during broker update: {e}")
#         raise
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()


def insert_broker(broker_data):
    """Insert broker with error handling or update if FCA_Registration_Number exists"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the FCA_Registration_Number already exists
        fca_registration = broker_data.get("FCA_Registration_Number")
        if fca_registration and fca_registration.strip():
            # Check if FCA Registration Number exists
            check_query = "SELECT Broker_ID FROM Broker WHERE FCA_Registration_Number = ?"
            cursor.execute(check_query, (fca_registration))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Record exists, perform an update instead of insert
                update_fields = {k: v for k, v in broker_data.items() 
                               if k not in ["Broker_ID", "FCA_Registration_Number"]}
                
                if update_fields:
                    set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
                    values = list(update_fields.values()) + [fca_registration]
                    update_query = f"UPDATE Broker SET {set_clause} WHERE FCA_Registration_Number = ?"
                    cursor.execute(update_query, values)
                    conn.commit()
                    return "updated"  # Return status to indicate an update occurred
                else:
                    return "no_changes"  # No changes to make
        
        # If we reach here, either no FCA_Registration_Number was provided or no existing record found
        # Proceed with insert
        insert_query = """
        INSERT INTO Broker (
            Broker_ID, Broker_Name, Commission, Date_Of_Onboarding,
            FCA_Registration_Number, Broker_Type, Market_Access, Delegated_Authority, Longevity_Years, Date_Of_Expiry, Status)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            broker_data.get("Broker_ID"),
            broker_data.get("Broker_Name"),
            broker_data.get("Commission"),
            broker_data.get("Date_Of_Onboarding"),
            fca_registration,
            broker_data.get("Broker_Type"),
            broker_data.get("Market_Access"),
            broker_data.get("Delegated_Authority"),
            broker_data.get("Longevity_Years"),
            broker_data.get("Date_Of_Expiry"),
            broker_data.get("Status", "Active")  # Default to Active if not provided
            
        )
        
        cursor.execute(insert_query, values)
        conn.commit()
        return "inserted"  # Return status to indicate an insert occurred
        
    except pyodbc.IntegrityError as e:
        if conn:
            conn.rollback()
        st.error(f"Broker data integrity error: {e}")
        st.info("💡 This usually means the Broker ID already exists")
        raise
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        st.error(f"Database error during broker operation: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Unexpected error during broker operation: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()


def insert_insurer(insurer_data):
    """Insert facility and multiple insurers with error handling"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert each insurer in the facility
        insurers = insurer_data.get('insurers', [])
        
        if not insurers:
            raise ValueError("No insurers provided in the data")

        # Find lead insurer (one with max participation)
        lead_insurer_id = max(insurers, key=lambda x: x.get('Participation', 0)).get('Insurer_ID')

        # Insert each insurer record
        for i, insurer in enumerate(insurers):
            insert_query = """
                INSERT INTO insurer (
                    Facility_ID, Facility_Name, Group_Size, Insurer_ID, Insurer_Name, Participation,
                    Date_Of_Onboarding, FCA_Registration_Number, Insurer_Type, Delegated_Authority, LeadInsurer,
                    Longevity_Years, Status, Date_Of_Expiry
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

            
            values = (
                insurer_data.get("Facility_ID"),
                insurer_data.get("Facility_Name"),
                insurer_data.get("Group_Size"),
                insurer.get("Insurer_ID"),
                insurer.get("Insurer_Name"),
                insurer.get("Participation"),
                insurer_data.get("Date_Of_Onboarding"),
                insurer.get("FCA_Registration_Number"),
                insurer.get("Insurer_Type"),
                insurer.get("Delegated_Authority"),
                1 if insurer.get("Insurer_ID") == lead_insurer_id else 0,
                insurer_data.get("Longevity_Years", 0),  # Default to 0 if not provided
                insurer.get("Status", "Active"),  # Default to Active if not provided
                insurer.get("Date_Of_Expiry", None)  # Default to None if not provided

            )

            
            try:
                cursor.execute(insert_query, values)
                st.info(f"✓ Inserted Insurer {i+1}: {insurer.get('Insurer_ID')} - {insurer.get('Insurer_Name')}")
                time.sleep(2)  # Pause briefly to show each success message
            except Exception as e:
                st.error(f"✗ Error inserting Insurer {i+1} ({insurer.get('Insurer_ID', 'Unknown')}): {e}")
                raise
        
        conn.commit()
        st.success(f"Successfully inserted all {len(insurers)} insurer(s) for facility {insurer_data.get('Facility_ID')}")
        time.sleep(5)  # Pause for a moment to let the user see the success message
        
    except pyodbc.IntegrityError as e:
        if conn:
            conn.rollback()
        st.error(f"Data integrity error: {e}")
        st.info("💡 This usually means duplicate IDs or constraint violations")
        raise
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        st.error(f"Database error: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Unexpected error: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()