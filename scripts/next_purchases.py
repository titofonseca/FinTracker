import sqlite3
from datetime import datetime, timedelta
import os
from collections import defaultdict
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_final_reits():
    logging.info("Recuperando lista de REITs da tabela final_ticker_list.")
    conn = get_db_connection()

    # Obtém os tickers da tabela final_ticker_list
    cursor = conn.execute('SELECT ticker FROM final_ticker_list')
    final_reits = [row[0] for row in cursor.fetchall()]

    conn.close()
    logging.info(f"Total de {len(final_reits)} REITs recuperados da tabela final_ticker_list.")
    return final_reits


def calculate_next_purchases():
    conn = get_db_connection()
    cur = conn.cursor()

    cash_balance_data = cur.execute("SELECT cash_balance FROM total_portfolio ORDER BY date DESC LIMIT 1").fetchone()
    cash_balance = cash_balance_data['cash_balance'] if cash_balance_data else 0

    best_reits_by_date = defaultdict(lambda: {'predicted_dividend': 0})

    final_reits = get_final_reits()  # Obtendo as tickers da tabela final

    for ticker in final_reits:
        latest_price_data = cur.execute("SELECT latest_price FROM recent_price WHERE ticker = ?", (ticker,)).fetchone()
        latest_price = latest_price_data['latest_price'] if latest_price_data else 0

        possible_buying_amount = cash_balance / latest_price if latest_price > 0 else 0

        dividend_data = cur.execute("SELECT ex_dividend_date, record_date, pay_date, dividend_amount FROM historic_dividends WHERE ticker = ? AND ex_dividend_date > ? ORDER BY ex_dividend_date ASC LIMIT 1", (ticker, datetime.today().strftime('%Y-%m-%d'))).fetchone()
        if dividend_data:
            next_ex_dividend_date = dividend_data['ex_dividend_date']
            next_record_date = dividend_data['record_date']
            next_pay_date = dividend_data['pay_date']
            next_dividend_amount = dividend_data['dividend_amount']

            predicted_dividend = possible_buying_amount * next_dividend_amount

            buy_on = datetime.strptime(next_ex_dividend_date, '%Y-%m-%d') - timedelta(days=1)
            sell_on = datetime.strptime(next_record_date, '%Y-%m-%d') if next_record_date else None

            if predicted_dividend > best_reits_by_date[next_ex_dividend_date]['predicted_dividend']:
                best_reits_by_date[next_ex_dividend_date] = {
                    'ticker': ticker,
                    'buy_on': buy_on.strftime('%Y-%m-%d'),
                    'sell_on': sell_on.strftime('%Y-%m-%d') if sell_on else None,
                    'next_pay_date': next_pay_date,
                    'cash_balance': cash_balance,
                    'possible_buying_amount': possible_buying_amount,
                    'predicted_dividend': predicted_dividend
                }

    sorted_reits = sorted(best_reits_by_date.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))

    for rank, (ex_div_date, data) in enumerate(sorted_reits, start=1):
        days_until_buy_on = (datetime.strptime(data['buy_on'], '%Y-%m-%d') - datetime.today()).days
        days_until_sell_on = (datetime.strptime(data['sell_on'], '%Y-%m-%d') - datetime.today()).days if data['sell_on'] else None
        days_until_next_pay_date = (datetime.strptime(data['next_pay_date'], '%Y-%m-%d') - datetime.today()).days if data['next_pay_date'] else None

        cur.execute('''INSERT OR REPLACE INTO next_purchases (ticker, buy_on, days_until_buy_on, sell_on, days_until_sell_on, next_pay_date, days_until_next_pay_date, cash_balance, possible_buying_amount, predicted_dividend, ranking)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (data['ticker'], data['buy_on'], days_until_buy_on, data['sell_on'], days_until_sell_on, data['next_pay_date'], days_until_next_pay_date, data['cash_balance'], data['possible_buying_amount'], data['predicted_dividend'], rank))

    conn.commit()
    conn.close()

def clear_next_purchases_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM next_purchases")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clear_next_purchases_table()
    calculate_next_purchases()
