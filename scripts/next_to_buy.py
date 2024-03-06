import sqlite3
from datetime import datetime, timedelta
import os

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Função para obter a lista de REITs negociados na eToro do banco de dados
def get_final_reits():
    conn = get_db_connection()
    cursor = conn.execute('SELECT ticker FROM final_ticker_list')
    final_reits = [row['ticker'] for row in cursor.fetchall()]
    conn.close()
    return final_reits

def calculate_next_to_buy():
    conn = get_db_connection()
    cur = conn.cursor()

    # Obter o cash_balance mais recente
    cash_balance_data = cur.execute("SELECT cash_balance FROM total_portfolio ORDER BY date DESC LIMIT 1").fetchone()
    cash_balance = cash_balance_data['cash_balance'] if cash_balance_data else 0

    # Lista para armazenar dados para classificação
    ranking_data = []

    final_reits = get_final_reits()  # Obtendo as tickers da tabela final

    for ticker in final_reits:
        # Obter o preço mais recente do REIT
        latest_price_data = cur.execute("SELECT latest_price FROM recent_price WHERE ticker = ?", (ticker,)).fetchone()
        latest_price = latest_price_data['latest_price'] if latest_price_data else 0

        # Calcular o número possível de ações a comprar
        cash_balance = round(cash_balance, 2)

        # Calcular o número possível de ações a comprar
        possible_buying_amount = cash_balance / latest_price if latest_price > 0 else 0
        # Obter dados sobre dividendos e datas relevantes
        dividend_data = cur.execute("SELECT ex_dividend_date, record_date, pay_date, dividend_amount FROM historic_dividends WHERE ticker = ? AND ex_dividend_date > ? ORDER BY ex_dividend_date ASC LIMIT 1", (ticker, datetime.today().strftime('%Y-%m-%d'))).fetchone()
        if dividend_data:
            next_ex_dividend_date = dividend_data['ex_dividend_date']
            next_record_date = dividend_data['record_date']
            next_pay_date = dividend_data['pay_date']
            next_dividend_amount = dividend_data['dividend_amount']

            # Calcular dias até as próximas datas relevantes
            days_until_next_ex_dividend = (datetime.strptime(next_ex_dividend_date, '%Y-%m-%d') - datetime.today()).days
            days_until_next_record_date = (datetime.strptime(next_record_date, '%Y-%m-%d') - datetime.today()).days +1 if next_record_date else None
            days_until_next_pay_date = (datetime.strptime(next_pay_date, '%Y-%m-%d') - datetime.today()).days +1 if next_pay_date else None
            
            # Calcular o dividendo previsto e o dividendo por dia
            predicted_dividend = possible_buying_amount * next_dividend_amount
            dividend_per_day = predicted_dividend / days_until_next_pay_date if days_until_next_pay_date else 0

            # Adicionar dados para ranking
            if days_until_next_ex_dividend is not None and days_until_next_ex_dividend >= 0:
                ranking_data.append((ticker, days_until_next_ex_dividend, predicted_dividend))
        else:
            # Se não houver dados de dividendos, definir valores padrão
            next_ex_dividend_date = None
            next_record_date = None
            next_pay_date = None
            days_until_next_ex_dividend = None
            days_until_next_record_date = None
            days_until_next_pay_date = None
            predicted_dividend = 0
            dividend_per_day = 0

        # Obter métricas de recuperação
        recovery_data = cur.execute("SELECT recovery_percentage, recovery_strength FROM recovery_metrics WHERE ticker = ?", (ticker,)).fetchone()
        recovery_percentage = recovery_data['recovery_percentage'] if recovery_data else 0
        recovery_strength = recovery_data['recovery_strength'] if recovery_data else 0

        # Inserir ou atualizar a linha na tabela next_to_buy
        cur.execute('''INSERT OR REPLACE INTO next_to_buy (ticker, next_ex_dividend_date, days_until_next_ex_dividend, next_record_date, days_until_next_record_date, next_pay_date, days_until_next_pay_date, cash_balance, possible_buying_amount, predicted_dividend, dividend_per_day, recovery_percentage, recovery_strength)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (ticker, next_ex_dividend_date, days_until_next_ex_dividend, next_record_date, days_until_next_record_date, next_pay_date, days_until_next_pay_date, cash_balance, possible_buying_amount, predicted_dividend, dividend_per_day, recovery_percentage, recovery_strength))

    # Ordenar os dados para ranking
    ranking_data.sort(key=lambda x: (x[1], -x[2]))

    # Aplicar ranking
    for i, (ticker, _, _) in enumerate(ranking_data):
        ranking = i + 1  # Ranking começa de 1
        cur.execute('''UPDATE next_to_buy SET ranking = ? WHERE ticker = ?''', (ranking, ticker))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    calculate_next_to_buy()
