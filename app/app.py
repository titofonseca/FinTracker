
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sys
import os
from datetime import datetime, timedelta
import asyncio
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determinar o caminho base, dependendo de como a aplicação está rodando
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Adicionando os diretórios necessários ao sys.path
sys.path.append(os.path.abspath(os.path.join(application_path, '..')))
sys.path.append(os.path.join(application_path, '..', 'db'))

# Agora as importações podem ser feitas normalmente
from refresh_all_tables import refresh_all_tables
from refresh_all_database import refresh_all_database
from refresh_all_prices import refresh_prices

import database

app = Flask(__name__)

# Função para formatar os dias até as datas importantes
def format_days(days):
    if days is None:
        return 'Date not available'  # Example default string
    elif days == 0:
        return 'Today'
    elif days == 1:
        return 'Tomorrow'
    elif days == -1:
        return 'Yesterday'
    elif days < 0:
        return f'{abs(days)} days ago'
    else:
        return f'In {days} days'

### --- Homepage: / --- ###

@app.route('/')
def index():
    return render_template('index.html')

### --- Buy / Sell Page: /wallet --- 

@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if request.method == 'POST':
        data = request.form['data']
        ticker = request.form['ticker']
        movimento = request.form['movimento']
        preco_inicial = request.form['preco_inicial']
        quantidade_inicial = request.form['quantidade_inicial']
        database.add_reit(data, ticker, movimento, preco_inicial, quantidade_inicial)
        return redirect(url_for('wallet'))

    reits = database.get_reits()
    return render_template('wallet.html', reits=reits)

@app.route('/delete_reit/<int:id>', methods=['POST'])
def delete_reit(id):
    database.delete_reit(id)
    return redirect(url_for('wallet'))

### --- Recieved Dividends Page: /dividends --- 

@app.route('/dividends', methods=['GET', 'POST'])
def dividends():
    if request.method == 'POST':
        data = request.form['data']
        ticker = request.form['ticker']
        amount = request.form['amount']
        database.add_dividend(data, ticker, amount)
        return redirect(url_for('dividends'))

    dividends = database.get_dividends()
    return render_template('recieved_dividends.html', dividends=dividends)

@app.route('/delete_dividend/<int:id>', methods=['POST'])
def delete_dividend(id):
    database.delete_dividend(id)
    return redirect(url_for('dividends'))

### --- Deposits / Withdrawals Page: /account_movements --- 

@app.route('/account_movements', methods=['GET', 'POST'])
def account_movements():
    if request.method == 'POST':
        data = request.form['data']
        movimento = request.form['movimento']
        amount = request.form['amount']
        database.add_account_movement(data, movimento, amount)
        return redirect(url_for('account_movements'))

    movements = database.get_account_movements()
    return render_template('account_movements.html', movements=movements)

@app.route('/delete_account_movement/<int:id>', methods=['POST'])
def delete_account_movement(id):
    database.delete_account_movement(id)
    return redirect(url_for('account_movements'))


### --- Dashboard --- ###

@app.route('/dashboard')
def dashboard():
    # Buscar dados do portfólio total
    portfolio = database.get_total_portfolio()

    reit_performance = database.get_reit_performance_data()


    # Buscar dados de desempenho de investimento
    raw_investment_performance_data = database.get_investment_performance_data()

    # Processar dados de desempenho de investimento
    investment_performance_data = []
    for reit in raw_investment_performance_data:
        reit_dict = dict(reit)
        for date_field in ['latest_record_date', 'latest_pay_date']:
            date_value = reit_dict.get(date_field)
            if date_value:
                reit_dict[f'days_until_{date_field}'] = (datetime.strptime(date_value, '%Y-%m-%d') - datetime.now()).days +1
            else:
                reit_dict[f'days_until_{date_field}'] = None
        ex_dividend_date = reit_dict.get('latest_ex_dividend_date')
        if ex_dividend_date:
            days_until_next_ex_dividend = (datetime.strptime(ex_dividend_date, '%Y-%m-%d') - datetime.now()).days
            reit_dict['days_until_next_ex_dividend'] = days_until_next_ex_dividend
            ex_div_minus_one = datetime.strptime(ex_dividend_date, '%Y-%m-%d') - timedelta(days=1)
            reit_dict['ex_div_minus_one'] = ex_div_minus_one.strftime('%Y-%m-%d')
        investment_performance_data.append(reit_dict)
    investment_performance_data.sort(key=lambda x: (x.get('days_until_next_ex_dividend', float('inf')) is None, x.get('days_until_next_ex_dividend', float('inf')) >= 0, abs(x.get('days_until_next_ex_dividend', 0))))

    # Buscar dados de dividendos recentes
    dividends_history_data = {
        'total_dividends': database.get_total_dividends(),
        'recent_dividends': database.get_recent_dividends()
    }

    # Buscar dados de transações recentes
    recent_transactions_data = database.get_recent_transactions()

    # Buscar dados de aquisições futuras
    upcoming_acquisitions_data = database.get_upcoming_acquisitions_data()

    # Converter objetos sqlite3.Row em dicionários
    upcoming_acquisitions_data = [dict(acquisition) for acquisition in upcoming_acquisitions_data]

    # Processar dados de aquisições futuras
    for acquisition in upcoming_acquisitions_data:
        next_ex_dividend_date = acquisition.get('next_ex_dividend_date')
        if next_ex_dividend_date:
            acquisition['ex_div_minus_one'] = (datetime.strptime(next_ex_dividend_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            acquisition['ex_div_minus_one'] = None

    # Calcular o balanço geral
    total_profit_loss = portfolio['total_profit_loss'] if portfolio['total_profit_loss'] is not None else 0
    total_dividends = dividends_history_data['total_dividends'] if dividends_history_data['total_dividends'] is not None else 0
    overall_balance = total_profit_loss + total_dividends

    # Formatar dados de balanço com sinal
    format_with_sign = lambda x: f"+{x:.2f}" if x >= 0 else f"{x:.2f}"

    # Preparar dados de balanço de investimentos para o frontend
    balance_investments_data = {
        'cash_balance': "{:.2f}".format(portfolio['cash_balance'] if portfolio['cash_balance'] is not None else 0),
        'total_investment': "{:.2f}".format(portfolio['total_investment'] if portfolio['total_investment'] is not None else 0),
        'total_current_value': "{:.2f}".format(portfolio['total_current_value'] if portfolio['total_current_value'] is not None else 0),
        'total_profit_loss': format_with_sign(total_profit_loss),
        'overall_balance': format_with_sign(overall_balance)
    }

    # Imprimir dados dos gráficos para os cartões
    card_graph_data = database.get_dashboard_card_graphs()

    dividends_history_graph = database.get_dividends_history()

    # Buscar dados de dividendos futuros qualificados
    future_dividends_data = database.get_qualified_future_dividends()
    total_future_dividends = sum(dividend['total_dividend_amount'] for dividend in future_dividends_data)

    # Buscar dados de dividendos futuros qualificados por data
    future_dividends_by_date = database.get_future_dividends_by_date()

    next_purchases_data = database.get_next_purchases()

    # Passar a função format_days para o template
    return render_template(
        'dashboard.html',
        dividends_history_graph=dividends_history_graph,
        balance_investments_data=balance_investments_data,
        investment_performance_data=investment_performance_data,
        dividends_history_data=dividends_history_data,
        recent_transactions_data=recent_transactions_data,
        upcoming_acquisitions_data=upcoming_acquisitions_data,
        card_graph_data=card_graph_data,
        future_dividends_data=future_dividends_data,
        total_future_dividends=total_future_dividends,
        future_dividends_by_date=future_dividends_by_date,
        next_purchases_data=next_purchases_data,
        reit_performance=reit_performance,
        format_days=format_days
    )

### --- Data for Graphic in Dashboard --- ###

@app.route('/refresh_all_tables', methods=['POST'])
def handle_refresh_tables():
    logger.info("Endpoint /refresh_all_tables chamado")
    try:
        asyncio.run(refresh_all_tables())
        return jsonify({"success": True}), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar tabelas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/refresh_all_database', methods=['POST'])
def handle_refresh_database():
    try:
        asyncio.run(refresh_all_database())  # Run the async function properly
        return jsonify({"success": True}), 200
    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/refresh_prices', methods=['POST'])
def handle_refresh_prices():
    try:
        asyncio.run(refresh_prices())
        return jsonify({"success": True}), 200
    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=False)

