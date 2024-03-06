import sqlite3
from pathlib import Path

def get_db_connection():
    """ Establishes a connection to the database. """
    conn = sqlite3.connect('db/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    
    conn.execute('''CREATE TABLE IF NOT EXISTS reit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT,
                        data TEXT,
                        movimento TEXT,
                        preco_inicial REAL,
                        quantidade_inicial REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS recieved_dividends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT,
                        data TEXT,
                        amount REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS account_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data TEXT,
                        movimento TEXT,
                        amount REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS historic_price (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT,
                        data TEXT,
                        close_price REAL,
                        open_price REAL,
                        highest_price REAL,
                        lowest_price REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS historic_dividends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT,
                        data TEXT,
                        record_date TEXT,
                        ex_dividend_date TEXT,
                        pay_date TEXT,
                        dividend_amount REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS reit_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT UNIQUE,
                        name TEXT,
                        homepage_url TEXT,
                        logo_url TEXT,
                        icon_url TEXT,
                        in_etoro TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS recent_price (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT UNIQUE,
                        date TEXT,
                        latest_price REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS total_portfolio (
                        date TEXT PRIMARY KEY,
                        total_investment REAL,
                        total_current_value REAL,
                        total_profit_loss REAL,
                        total_dividend_cashed REAL,
                        cash_balance REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS latest_data (
                        ticker TEXT PRIMARY KEY,
                        latest_price REAL,
                        latest_ex_dividend_date TEXT,
                        latest_record_date TEXT,
                        latest_pay_date TEXT,
                        latest_yield REAL,
                        latest_dividend_amount REAL,
                        in_wallet TEXT,
                        amount_in_wallet REAL,
                        average_buy_price REAL,
                        total_investment REAL,
                        expected_dividend_amount REAL,
                        current_value REAL,
                        profit_loss REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS hold_or_sell (
                        ticker TEXT PRIMARY KEY,
                        in_wallet TEXT,
                        status TEXT,
                        current_llv REAL,
                        target_llv REAL,
                        investment REAL,
                        current_value REAL,
                        expected_dividend REAL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS recovery_metrics (
                        ticker TEXT PRIMARY KEY,
                        recovery_percentage REAL,
                        recovery_strength REAL,
                        last_recovery_time TEXT,
                        num_dividends_paid INTEGER,
                        num_recoveries INTEGER,
                        min_recovery_time TEXT,
                        max_recovery_time TEXT,
                        avg_recovery_time TEXT,
                        num_7day_recoveries INTEGER,
                        min_7day_recovery_time TEXT,
                        max_7day_recovery_time TEXT,
                        avg_7day_recovery_time TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS next_to_buy (
                        ticker TEXT PRIMARY KEY,
                        next_ex_dividend_date TEXT,
                        days_until_next_ex_dividend INTEGER,
                        next_record_date TEXT,
                        days_until_next_record_date INTEGER,
                        next_pay_date TEXT,
                        days_until_next_pay_date INTEGER,
                        cash_balance REAL,
                        possible_buying_amount REAL,
                        predicted_dividend REAL,
                        dividend_per_day REAL,
                        recovery_percentage REAL,
                        recovery_strength REAL,
                        ranking INTEGER)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS next_purchases (
                        ticker TEXT PRIMARY KEY,
                        buy_on TEXT, 
                        days_until_buy_on INTEGER,
                        sell_on TEXT,
                        days_until_sell_on INTEGER,
                        next_pay_date TEXT,
                        days_until_next_pay_date INTEGER,
                        cash_balance REAL,
                        possible_buying_amount REAL,
                        predicted_dividend REAL,
                        ranking INTEGER)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS all_etoro_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT UNIQUE,
                        recent_price REAL,
                        price_date TEXT,
                        recent_dividend REAL,
                        dividend_date TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS final_ticker_list (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT UNIQUE)''')
    
    conn.commit()
    conn.close()

# Add Transactions Page def's: app/templates/wallet.html

# @app.route('/wallet', methods=['GET', 'POST'])
       
def add_reit(data, ticker, movimento, preco_inicial, quantidade_inicial):
    conn = get_db_connection()
    conn.execute('INSERT INTO reit (data, ticker, movimento, preco_inicial, quantidade_inicial) VALUES (?, ?, ?, ?, ?)',
                 (data, ticker, movimento, preco_inicial, quantidade_inicial))
    conn.commit()
    conn.close()

def get_reits():
    conn = get_db_connection()
    reits = conn.execute('SELECT * FROM reit').fetchall()
    conn.close()
    return reits

# @app.route('/delete_reit/<int:id>', methods=['POST'])

def delete_reit(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM reit WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Recieved Dividends Page def's: app/templates/recieved_dividends.html

# @app.route('/dividends', methods=['GET', 'POST'])
    
def add_dividend(data, ticker, amount):
    conn = get_db_connection()
    conn.execute('INSERT INTO recieved_dividends (data, ticker, amount) VALUES (?, ?, ?)',
                 (data, ticker, amount))
    conn.commit()
    conn.close()

def get_dividends():
    conn = get_db_connection()
    dividends = conn.execute('SELECT * FROM recieved_dividends').fetchall()
    conn.close()
    return dividends

# @app.route('/delete_dividend/<int:id>', methods=['POST'])

def delete_dividend(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM recieved_dividends WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Account Movements Page def's: app/templates/account_movements.html
    
# @app.route('/account_movements', methods=['GET', 'POST'])

def add_account_movement(data, movimento, amount):
    conn = get_db_connection()
    conn.execute('INSERT INTO account_movements (data, movimento, amount) VALUES (?, ?, ?)',
                 (data, movimento, amount))
    conn.commit()
    conn.close()

def get_account_movements():
    conn = get_db_connection()
    movements = conn.execute('SELECT * FROM account_movements').fetchall()
    conn.close()
    return movements

# @app.route('/delete_account_movement/<int:id>', methods=['POST'])

def delete_account_movement(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM account_movements WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Historic Prices API access .py File: scripts/historic_price.py
    
def add_historic_price(ticker, data, close_price, open_price, highest_price, lowest_price):
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM historic_price WHERE ticker = ? AND data = ?',
                            (ticker, data)).fetchone()
    if not existing:
        conn.execute('INSERT INTO historic_price (ticker, data, close_price, open_price, highest_price, lowest_price) VALUES (?, ?, ?, ?, ?, ?)',
                     (ticker, data, close_price, open_price, highest_price, lowest_price))
        conn.commit()
    conn.close()

# Historic Dividend API access .py File: scripts/historic_dividend.py

def add_historic_dividend(ticker, data, record_date, ex_dividend_date, pay_date, dividend_amount):
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM historic_dividends WHERE ticker = ? AND data = ? AND record_date = ? AND ex_dividend_date = ?',
                            (ticker, data, record_date, ex_dividend_date)).fetchone()
    if not existing:
        conn.execute('INSERT INTO historic_dividends (ticker, data, record_date, ex_dividend_date, pay_date, dividend_amount) VALUES (?, ?, ?, ?, ?, ?)',
                     (ticker, data, record_date, ex_dividend_date, pay_date, dividend_amount))
        conn.commit()
    conn.close()

# Recent Prices API access .py File: scripts/recent_price.py

def add_or_update_recent_price(ticker, date, latest_price):
    conn = get_db_connection()
    conn.execute('''INSERT OR REPLACE INTO recent_price (ticker, date, latest_price)
                    VALUES (?, ?, ?)''',
                 (ticker, date, latest_price))
    conn.commit()
    conn.close()

# REIT Info API access .py File: scripts/reit_info.py

def add_or_update_reit_info(ticker, name, homepage_url, logo_url, icon_url):
    conn = get_db_connection()
    conn.execute('''INSERT OR REPLACE INTO reit_info (ticker, name, homepage_url, logo_url, icon_url)
                    VALUES (?, ?, ?, ?, ?)''',
                 (ticker, name, homepage_url, logo_url, icon_url))
    conn.commit()
    conn.close()

# Latest Data .py File: scripts/latest_data.py

def get_latest_data():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM latest_data').fetchall()
    conn.close()
    return data

## DASHBOARD ##
    
def get_total_portfolio():
    conn = get_db_connection()
    portfolio = conn.execute('SELECT * FROM total_portfolio ORDER BY date DESC LIMIT 1').fetchone()
    conn.close()
    return portfolio

def get_total_dividends():
    conn = get_db_connection()
    total = conn.execute('SELECT SUM(amount) as total FROM recieved_dividends').fetchone()
    conn.close()
    return total['total'] if total['total'] is not None else 0

def get_recent_dividends():
    conn = get_db_connection()
    dividends = conn.execute('''
        SELECT rd.*, ri.icon_url, ri.logo_url FROM recieved_dividends rd
        INNER JOIN reit_info ri ON rd.ticker = ri.ticker
        ORDER BY rd.data DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return dividends

def get_dividends_history():
    conn = get_db_connection()
    query = '''
        SELECT data, SUM(amount) as total_amount
        FROM recieved_dividends
        GROUP BY data
        ORDER BY data
    '''
    dividends_history = conn.execute(query).fetchall()
    conn.close()
    return [{'date': row['data'], 'total_amount': row['total_amount']} for row in dividends_history]

def get_investment_performance_data():
    conn = get_db_connection()
    query = '''
        SELECT 
            ld.ticker,
            ld.amount_in_wallet,
            ld.average_buy_price,
            ld.total_investment,
            ld.current_value,
            ld.profit_loss,
            ld.latest_price,
            ld.latest_ex_dividend_date,
            ld.latest_dividend_amount,
            ld.latest_record_date,
            ld.latest_pay_date,
            hos.expected_dividend,  
            hos.target_llv,         
            hos.current_llv,        
            hos.status,             
            ri.icon_url, 
            ri.logo_url,
            MAX(r.preco_inicial) as highest_initial_price
        FROM latest_data ld
        LEFT JOIN reit_info ri ON ld.ticker = ri.ticker
        LEFT JOIN hold_or_sell hos ON ld.ticker = hos.ticker
        LEFT JOIN reit r ON ld.ticker = r.ticker
        WHERE ld.amount_in_wallet > 0
        GROUP BY ld.ticker
    '''
    data = conn.execute(query).fetchall()
    conn.close()
    return data

def get_recent_transactions():
    conn = get_db_connection()
    transactions = conn.execute('''
        SELECT r.*, ri.icon_url, ri.logo_url FROM reit r
        INNER JOIN reit_info ri ON r.ticker = ri.ticker
        ORDER BY r.data DESC LIMIT 5
    ''').fetchall()
    conn.close()
    return transactions

def get_upcoming_acquisitions_data():
    conn = get_db_connection()
    query = '''
        SELECT nt.*, ri.icon_url, ri.logo_url, ri.name FROM next_to_buy nt
        LEFT JOIN reit_info ri ON nt.ticker = ri.ticker
        ORDER BY nt.ranking
    '''
    acquisitions = conn.execute(query).fetchall()
    conn.close()
    return acquisitions

def get_recent_prices():
    conn = get_db_connection()
    prices = conn.execute('SELECT * FROM recent_price').fetchall()
    conn.close()
    return prices

def get_dashboard_card_graphs():
    conn = get_db_connection()

    def fetch_graph_data(metric):
        query = f"""
        SELECT date, {metric} 
        FROM total_portfolio 
        WHERE date >= DATE('now', '-30 days')
        ORDER BY date
        """
        return [dict(row) for row in conn.execute(query).fetchall()]

    cash_flow_data = fetch_graph_data("cash_balance")
    full_investment_data = fetch_graph_data("total_investment")
    current_value_data = fetch_graph_data("total_current_value")
    pl_absolute_data = fetch_graph_data("total_profit_loss")
    overall_balance_data = fetch_graph_data("total_profit_loss + total_dividend_cashed")

    conn.close()

    return {
        "cash_flow": cash_flow_data,
        "full_investment": full_investment_data,
        "current_value": current_value_data,
        "pl_absolute": pl_absolute_data,
        "overall_balance": overall_balance_data
    }

def get_graph_data(days):
    conn = get_db_connection()
    # Verifique se a data é calculada corretamente
    date_query = conn.execute("SELECT DATE('now', ?)", ('-' + str(days) + ' days',)).fetchone()

    query = '''
        SELECT date, total_current_value FROM total_portfolio
        WHERE date >= DATE('now', '-' || ? || ' days')
        ORDER BY date ASC
    '''
    data = conn.execute(query, (str(days),)).fetchall()
    conn.close()

    graph_data = {
        "dates": [row['date'] for row in data],
        "values": [float(row['total_current_value']) for row in data]
    }

    return graph_data

def get_qualified_future_dividends():
    conn = get_db_connection()
    query = '''
        SELECT 
            hd.ticker, 
            hd.pay_date, 
            hd.dividend_amount * r.total_quantity AS total_dividend_amount,
            ri.icon_url, 
            ri.logo_url
        FROM historic_dividends hd
        INNER JOIN reit_info ri ON hd.ticker = ri.ticker
        INNER JOIN (
            SELECT 
                ticker, 
                SUM(CASE WHEN movimento = 'Compra' THEN quantidade_inicial END) AS total_quantity
            FROM reit
            GROUP BY ticker
        ) r ON hd.ticker = r.ticker
        WHERE hd.pay_date > DATE('now')
        AND NOT EXISTS (
            SELECT 1 FROM recieved_dividends rd 
            WHERE hd.ticker = rd.ticker AND hd.pay_date = rd.data
        )
        GROUP BY hd.ticker, hd.pay_date, hd.dividend_amount, ri.icon_url, ri.logo_url
        ORDER BY hd.pay_date
    '''
    future_dividends = conn.execute(query).fetchall()
    conn.close()
    return future_dividends


def get_future_dividends_by_date():
    conn = get_db_connection()
    query = '''
        SELECT 
            hd.pay_date, 
            SUM(hd.dividend_amount * r.total_quantity) AS total_dividend_amount
        FROM historic_dividends hd
        LEFT JOIN (
            SELECT 
                ticker, 
                SUM(CASE WHEN movimento = 'Compra' THEN quantidade_inicial END) AS total_quantity
            FROM reit
            GROUP BY ticker
        ) r ON hd.ticker = r.ticker
        WHERE hd.pay_date > DATE('now') 
        GROUP BY hd.pay_date
        ORDER BY hd.pay_date
    '''
    future_dividends_by_date = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in future_dividends_by_date]

def get_next_purchases():
    conn = get_db_connection()
    next_purchases = conn.execute('''
        SELECT np.*, ri.icon_url, ri.logo_url 
        FROM next_purchases np
        LEFT JOIN reit_info ri ON np.ticker = ri.ticker
        ORDER BY np.ranking ASC
    ''').fetchall()
    conn.close()
    return next_purchases

def calculate_break_even(initial_price, dividend_per_share):
    return initial_price - dividend_per_share

def calculate_scaled_prices(initial_price, dividend_per_share, profit_percentage):
    return (dividend_per_share * profit_percentage / 100) + initial_price - dividend_per_share

def get_reit_performance_data():
    conn = get_db_connection()
    query = '''
        SELECT
            r.ticker,
            SUM(CASE WHEN r.movimento = 'Compra' THEN r.quantidade_inicial ELSE -r.quantidade_inicial END) as quantidade_atual,
            r.preco_inicial,
            hd.dividend_amount,
            ri.logo_url,
            ri.icon_url,
            ld.latest_price
        FROM reit r
        JOIN historic_dividends hd ON r.ticker = hd.ticker
        JOIN reit_info ri ON r.ticker = ri.ticker
        JOIN latest_data ld ON r.ticker = ld.ticker
        GROUP BY r.ticker
        HAVING quantidade_atual > 0
    '''
    reits_data = conn.execute(query).fetchall()
    conn.close()

    performance_data = []
    for reit in reits_data:
        data = {
            'ticker': reit['ticker'],
            'initial_price': reit['preco_inicial'],
            'dividend_per_share': reit['dividend_amount'],
            'break_even': calculate_break_even(reit['preco_inicial'], reit['dividend_amount']),
            'scaled_prices': {percent: calculate_scaled_prices(reit['preco_inicial'], reit['dividend_amount'], percent) for percent in range(10, 101, 10)},
            'logo_url': reit['logo_url'],
            'icon_url': reit['icon_url'],
            'latest_price': reit['latest_price']
        }
        performance_data.append(data)

    return performance_data

create_tables()