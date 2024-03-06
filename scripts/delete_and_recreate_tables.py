import sqlite3
from database import create_tables  # Importa a função create_tables do seu arquivo database.py

def delete_and_recreate_tables():
    """
    Deletes all tables from the database except specific ones,
    then recreates all tables.
    """
    tables_to_exclude = ["reit", "recieved_dividends", "account_movements", "sqlite_sequence"]

    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()

    try:
        # Delete tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            if table_name not in tables_to_exclude:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                print(f"Table '{table_name}' deleted successfully.")
            else:
                print(f"Skipping deletion of table '{table_name}'.")

        # Recreate tables
        create_tables()  # Chamando a função create_tables do arquivo database.py
        print("All tables recreated successfully.")
        conn.commit()
    except Exception as e:
        print("Error deleting and recreating tables:", e)
    finally:
        conn.close()

# Main entry point of the script
if __name__ == '__main__':
    delete_and_recreate_tables()
