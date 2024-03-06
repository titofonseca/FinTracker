import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_status_and_llv(ticker, conn):
    # Obter dados mais recentes do REIT
    latest_data = conn.execute('SELECT * FROM latest_data WHERE ticker = ?', (ticker,)).fetchone()
    if not latest_data:
        return None

    # Verificar se o REIT está na carteira
    in_wallet = latest_data['in_wallet']
    current_value = latest_data['current_value']
    total_investment = latest_data['total_investment']
    expected_dividend = latest_data['expected_dividend_amount']
    current_llv = current_value + expected_dividend - total_investment
    target_llv = expected_dividend * 0.9

    # Verificar datas para determinar o status
    today = datetime.now().date()
    ex_div_date = datetime.strptime(latest_data['latest_ex_dividend_date'], '%Y-%m-%d').date() if latest_data['latest_ex_dividend_date'] else None
    record_date = datetime.strptime(latest_data['latest_record_date'], '%Y-%m-%d').date() if latest_data['latest_record_date'] else None

    if ex_div_date and ex_div_date > today:
        status = 'Pre Ex Div'
    elif record_date and record_date > today:
        status = 'Pre Record'
    else:
        status = 'Sell' if current_llv >= target_llv else 'Hold'

    return in_wallet, status, current_llv, target_llv, total_investment, current_value, expected_dividend

def update_hold_or_sell_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obter a lista de todos os REITs
    tickers = cursor.execute('SELECT ticker FROM latest_data').fetchall()

    for ticker_row in tickers:
        ticker = ticker_row['ticker']
        result = calculate_status_and_llv(ticker, conn)

        if result:
            in_wallet, status, current_llv, target_llv, investment, current_value, expected_dividend = result
            cursor.execute('''INSERT OR REPLACE INTO hold_or_sell (ticker, in_wallet, status, current_llv, target_llv, investment, current_value, expected_dividend)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                            (ticker, in_wallet, status, current_llv, target_llv, investment, current_value, expected_dividend))

    conn.commit()
    conn.close()

update_hold_or_sell_table()
