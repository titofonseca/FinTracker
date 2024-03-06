import sqlite3

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    conn = sqlite3.connect('db/database.db')
    return conn

def delete_tables(table_names):
    """
    Deletes multiple tables from the database.
    """
    conn = get_db_connection()
    try:
        for table_name in table_names:
            # Builds the SQL statement safely to avoid SQL Injection
            sql = f'DROP TABLE IF EXISTS {table_name}'
            conn.execute(sql)
            print(f"Table '{table_name}' deleted successfully.")
        conn.commit()
    except Exception as e:
        print("Error deleting tables:", e)
    finally:
        conn.close()

# Define the names of the tables here
tables_to_delete = ["recovery_metrics", "next_purchases", "all_etoro_data","historic_price","historic_dividends","recent_price","total_portfolio","latest_data","hold_or_sell","next_to_buy","final_ticker_list","reit_info"]

# Executes the function to delete the tables
delete_tables(tables_to_delete)