import sqlite3

def get_all_tables(conn):
    """ Retorna uma lista de nomes de todas as tabelas no banco de dados. """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def print_table_info(conn, table_name):
    """ Imprime informações sobre uma tabela. """
    cursor = conn.cursor()
    # Obter o cabeçalho
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 0;")
    col_names = [desc[0] for desc in cursor.description]
    print(f"\nTabela: {table_name}")
    print("Cabeçalho:", col_names)
    
    # Obter a primeira linha
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
    first_row = cursor.fetchone()
    print("Primeira linha:", first_row)

    # Contar o número de linhas
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = cursor.fetchone()[0]
    print("Número total de linhas:", row_count)

def main():
    database_path = 'db/database.db' # Substitua pelo caminho correto do seu banco de dados
    conn = sqlite3.connect(database_path)
    
    try:
        tables = get_all_tables(conn)
        for table in tables:
            print_table_info(conn, table)
    finally:
        conn.close()

if __name__ == "__main__":
    main()