import sqlite3
import csv
import os

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    return conn

def get_all_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def export_table_to_csv(table_name, folder_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    file_path = os.path.join(folder_name, f'{table_name}.csv')

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(columns)  # write headers
        for row in rows:
            csvwriter.writerow(row)

    conn.close()

def main():
    folder_name = 'exported_tables'
    conn = get_db_connection()
    tables = get_all_table_names(conn)

    for table in tables:
        export_table_to_csv(table, folder_name)
        print(f"Exported {table} to CSV in '{folder_name}' folder.")

    conn.close()

if __name__ == '__main__':
    main()
