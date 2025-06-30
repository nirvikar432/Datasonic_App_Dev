from db_utils import execute_query

def update_policy_lapsed_status():
    sql = """
    UPDATE dbo.Policy
    SET isLapsed = 
        CASE 
            WHEN CAST(GETDATE() AS DATE) < POL_EFF_DATE 
              OR CAST(GETDATE() AS DATE) > POL_EXPIRY_DATE 
            THEN 1
            ELSE 0
        END;
    """
    execute_query(sql)