import sqlite3
from datetime import datetime, timedelta
from tqdm import tqdm


def get_db_connection():
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_cash_balance(cur, date_str):
    cash_balance = 0

    # Soma de todos os depósitos e subtração de todos os levantamentos até a data
    cur.execute("SELECT movimento, amount FROM account_movements WHERE data <= ?", (date_str,))
    movimentos = cur.fetchall()
    for movimento in movimentos:
        if movimento['movimento'] == 'Deposit':
            cash_balance += movimento['amount']
        elif movimento['movimento'] == 'Withdraw':
            cash_balance -= movimento['amount']

    # Subtrair o valor de todas as compras e adicionar o valor de todas as vendas até a data
    cur.execute("SELECT movimento, preco_inicial, quantidade_inicial FROM reit WHERE data <= ?", (date_str,))
    transacoes = cur.fetchall()
    for transacao in transacoes:
        valor_transacao = transacao['preco_inicial'] * transacao['quantidade_inicial']
        if transacao['movimento'] == 'Compra':
            cash_balance -= valor_transacao
        elif transacao['movimento'] == 'Venda':
            cash_balance += valor_transacao

    # Adicionar os dividendos recebidos até a data
    cur.execute("SELECT SUM(amount) FROM recieved_dividends WHERE data <= ?", (date_str,))
    dividendos = cur.fetchone()[0] or 0
    cash_balance += dividendos

    return cash_balance

def calculate_total_investment(cur, date_str):
    total_investment = 0
    cur.execute("SELECT movimento, preco_inicial, quantidade_inicial FROM reit WHERE data <= ?", (date_str,))
    transacoes = cur.fetchall()
    for transacao in transacoes:
        valor_transacao = transacao['preco_inicial'] * transacao['quantidade_inicial']
        if transacao['movimento'] == 'Compra':
            total_investment += valor_transacao
        elif transacao['movimento'] == 'Venda':
            total_investment -= valor_transacao
    return total_investment

def calculate_total_current_value(cur, date_str):
    total_current_value = 0
    cur.execute("SELECT ticker, SUM(CASE WHEN movimento = 'Compra' THEN quantidade_inicial ELSE -quantidade_inicial END) AS quantidade_liquida FROM reit WHERE data <= ? GROUP BY ticker", (date_str,))
    quantidades = cur.fetchall()
    for q in quantidades:
        cur.execute("SELECT close_price FROM historic_price WHERE ticker = ? AND data = ? ORDER BY data DESC LIMIT 1", (q['ticker'], date_str))
        price_info = cur.fetchone()
        if price_info:
            total_current_value += price_info['close_price'] * q['quantidade_liquida']
        else:
            cur.execute("SELECT latest_price FROM recent_price WHERE ticker = ? ORDER BY date DESC LIMIT 1", (q['ticker'],))
            latest_price_info = cur.fetchone()
            if latest_price_info:
                total_current_value += latest_price_info['latest_price'] * q['quantidade_liquida']
    return total_current_value

def calculate_total_dividend_cashed(cur, date_str):
    cur.execute("SELECT SUM(amount) FROM recieved_dividends WHERE data <= ?", (date_str,))
    dividendos = cur.fetchone()[0] or 0
    return dividendos

def calculate_and_insert_portfolio_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Verificar se a coluna total_realized_profit_loss existe na tabela total_portfolio
    columns = conn.execute("PRAGMA table_info(total_portfolio)").fetchall()
    if not any(column[1] == 'total_realized_profit_loss' for column in columns):
        cur.execute("ALTER TABLE total_portfolio ADD COLUMN total_realized_profit_loss REAL DEFAULT 0")

    # Determinar o intervalo de datas para os cálculos
    cur.execute("SELECT MIN(data) AS start_date, MAX(data) AS end_date FROM reit")
    dates = cur.fetchone()
    if not dates['start_date'] or not dates['end_date']:
        print("Não há dados suficientes para calcular o portfólio.")
        conn.close()
        return

    start_date = datetime.strptime(dates['start_date'], '%Y-%m-%d')
    end_date = datetime.today()
    delta = timedelta(days=1)

    # Calcular o número total de dias para a barra de progresso
    total_days = (end_date - start_date).days + 1

    # Iterar por cada dia com uma barra de progresso
    for _ in tqdm(range(total_days), desc="Processando dados do portfólio"):
        date_str = start_date.strftime('%Y-%m-%d')

    # Iterar por cada dia
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        cash_balance = calculate_cash_balance(cur, date_str)
        total_investment = calculate_total_investment(cur, date_str)
        total_current_value = calculate_total_current_value(cur, date_str)
        total_dividend_cashed = calculate_total_dividend_cashed(cur, date_str)

        # Calcular o lucro/prejuízo total
        total_profit_loss = total_current_value - total_investment

        # Calcular o total_realized_profit_loss
        total_deposited = sum(mov['amount'] for mov in cur.execute("SELECT amount FROM account_movements WHERE movimento = 'Deposit' AND data <= ?", (date_str,)).fetchall())
        total_withdrawn = sum(mov['amount'] for mov in cur.execute("SELECT amount FROM account_movements WHERE movimento = 'Withdraw' AND data <= ?", (date_str,)).fetchall())
        total_realized_profit_loss = (total_current_value + cash_balance + total_withdrawn) - total_deposited

        # Inserir ou atualizar os dados no total_portfolio
        cur.execute("INSERT OR REPLACE INTO total_portfolio (date, total_investment, total_current_value, total_profit_loss, total_dividend_cashed, cash_balance, total_realized_profit_loss) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (date_str, total_investment, total_current_value, total_profit_loss, total_dividend_cashed, cash_balance, total_realized_profit_loss))
        conn.commit()

        current_date += delta

    conn.close()

if __name__ == '__main__':
    calculate_and_insert_portfolio_data()
