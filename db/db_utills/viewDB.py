import sqlite3

def query_database():
    conn = sqlite3.connect('db/database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM historic_price")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    conn.close()

query_database()