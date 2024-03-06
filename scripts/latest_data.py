import sqlite3
from tqdm import tqdm

def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def update_latest_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Obter lista de todos os tickers
    cur.execute("SELECT DISTINCT ticker FROM reit")
    tickers = [row['ticker'] for row in cur.fetchall()]

    # Adicionando a barra de progresso para o loop dos tickers
    for ticker in tqdm(tickers, desc="Updating latest data"):
        # Obter o preço mais recente e dados de dividendos
        cur.execute("SELECT * FROM recent_price WHERE ticker = ?", (ticker,))
        recent_data = cur.fetchone()

        cur.execute("SELECT * FROM historic_dividends WHERE ticker = ? ORDER BY pay_date DESC LIMIT 1", (ticker,))
        recent_dividend_data = cur.fetchone()

        # Obter dados da carteira
        cur.execute("""
            SELECT SUM(CASE WHEN movimento = 'Compra' THEN quantidade_inicial ELSE -quantidade_inicial END) as quantidade_liquida,
                   AVG(preco_inicial) as average_buy_price
            FROM reit WHERE ticker = ?""", (ticker,))
        wallet_data = cur.fetchone()

        in_wallet = 'Y' if wallet_data and wallet_data['quantidade_liquida'] > 0 else 'N'
        amount_in_wallet = wallet_data['quantidade_liquida'] if wallet_data and in_wallet == 'Y' else 0
        average_buy_price = wallet_data['average_buy_price'] if wallet_data and in_wallet == 'Y' else 0
        total_investment = average_buy_price * amount_in_wallet if wallet_data else 0

        # Calcular valores
        latest_price = recent_data['latest_price'] if recent_data else 0
        latest_dividend_amount = recent_dividend_data['dividend_amount'] if recent_dividend_data else 0
        expected_dividend_amount = latest_dividend_amount * amount_in_wallet
        current_value = latest_price * amount_in_wallet
        profit_loss = current_value - total_investment

        # Inserir/atualizar na tabela latest_data
        cur.execute('''
            INSERT OR REPLACE INTO latest_data (ticker, latest_price, latest_ex_dividend_date, latest_record_date, latest_pay_date, latest_yield, latest_dividend_amount, in_wallet, amount_in_wallet, average_buy_price, total_investment, expected_dividend_amount, current_value, profit_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (ticker, latest_price, recent_dividend_data['ex_dividend_date'] if recent_dividend_data else None, recent_dividend_data['record_date'] if recent_dividend_data else None, recent_dividend_data['pay_date'] if recent_dividend_data else None, None, latest_dividend_amount, in_wallet, amount_in_wallet, average_buy_price, total_investment, expected_dividend_amount, current_value, profit_loss))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_latest_data()
