import sqlite3
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Função para obter a lista de REITs negociados na eToro do banco de dados
def get_final_reits():
    conn = get_db_connection()
    cursor = conn.execute('SELECT ticker FROM final_ticker_list')
    final_reits = [row[0] for row in cursor.fetchall()]
    conn.close()
    return final_reits

def calculate_recovery_metrics(ticker):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obter dados históricos de dividendos e preços
    cur.execute("SELECT * FROM historic_dividends WHERE ticker = ?", (ticker,))
    dividend_data = cur.fetchall()

    recovery_counts = []
    recovery_times = []
    recovery_times_7day = []

    for dividend in dividend_data:
        ex_div_date = datetime.strptime(dividend['ex_dividend_date'], '%Y-%m-%d')
        cur.execute("SELECT close_price FROM historic_price WHERE ticker = ? AND data < ? ORDER BY data DESC LIMIT 1", (ticker, dividend['ex_dividend_date']))
        pre_ex_div_price_data = cur.fetchone()
        if not pre_ex_div_price_data:
            continue

        pre_ex_div_price = pre_ex_div_price_data['close_price']
        recovered = False
        recovered_within_7_days = False
        recovery_time = None

        for i in range(30):  # Considerando um período de 30 dias para recuperação
            check_date = ex_div_date + timedelta(days=i)
            cur.execute("SELECT close_price FROM historic_price WHERE ticker = ? AND data = ?", (ticker, check_date.strftime('%Y-%m-%d')))
            check_price_data = cur.fetchone()
            if check_price_data and check_price_data['close_price'] >= pre_ex_div_price:
                recovered = True
                recovery_time = i
                recovery_times.append(i)
                if i <= 7:
                    recovered_within_7_days = True
                    recovery_times_7day.append(i)
                break

        if recovered:
            recovery_counts.append(1 if recovered_within_7_days else 0)

    # Calcular métricas
    num_dividends_paid = len(dividend_data)
    num_recoveries = sum(recovery_counts)
    num_7day_recoveries = len([time for time in recovery_times if time <= 7])

    min_recovery_time = min(recovery_times) if recovery_times else "Never"
    max_recovery_time = max(recovery_times) if recovery_times else "Never"
    avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else "Never"

    min_7day_recovery_time = min(recovery_times_7day) if recovery_times_7day else "Never"
    max_7day_recovery_time = max(recovery_times_7day) if recovery_times_7day else "Never"
    avg_7day_recovery_time = sum(recovery_times_7day) / len(recovery_times_7day) if recovery_times_7day else "Never"

    recovery_percentage = (num_7day_recoveries / num_dividends_paid) * 100 if num_dividends_paid > 0 else 0
    recovery_strength = sum(recovery_counts) / len(recovery_counts) if recovery_counts else 0

    # Última recuperação
    last_recovery_time = recovery_times[-1] if recovery_times else "Didn't Recover"

    # Inserir dados na tabela recovery_metrics
    cur.execute('''INSERT OR REPLACE INTO recovery_metrics (ticker, recovery_percentage, recovery_strength, last_recovery_time, num_dividends_paid, num_recoveries, min_recovery_time, max_recovery_time, avg_recovery_time, num_7day_recoveries, min_7day_recovery_time, max_7day_recovery_time, avg_7day_recovery_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (ticker, recovery_percentage, recovery_strength, last_recovery_time, num_dividends_paid, num_recoveries, min_recovery_time, max_recovery_time, avg_recovery_time, num_7day_recoveries, min_7day_recovery_time, max_7day_recovery_time, avg_7day_recovery_time))

    conn.commit()
    conn.close()

def update_recovery_metrics():
    final_reits = get_final_reits()
    for ticker in final_reits:
        calculate_recovery_metrics(ticker)

if __name__ == "__main__":
    update_recovery_metrics()