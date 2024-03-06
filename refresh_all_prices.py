import os
import sys
import asyncio

# Adicionando o diretório de scripts ao path para importar os módulos
scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.append(scripts_path)

from scripts import reit_info
from scripts import recent_price
from scripts import historic_price
from scripts import historic_dividend
import scripts.pick_tickers as pick_tickers
import scripts.latest_data as latest_data_script
import scripts.total_portfolio as total_portfolio_script
import scripts.hold_or_sell as hold_or_sell_script
import scripts.recovery_metrics as recovery_metrics_script
import scripts.next_to_buy as next_to_buy_script
import scripts.next_purchases as next_purchases

async def refresh_prices():
    print("Updating...\n")

    # Call the pick_tickers first
    #await pick_tickers.main()

    # The rest of the update functions
    #await reit_info.main()
    await recent_price.main()
    #await historic_price.main()
    #await historic_dividend.main()

    # Assuming latest_data_script.update_latest_data() and the following functions are synchronous,
    # you don't need to do anything special for them.
    latest_data_script.update_latest_data()
    total_portfolio_script.calculate_and_insert_portfolio_data()
    hold_or_sell_script.update_hold_or_sell_table()
    #recovery_metrics_script.update_recovery_metrics()
    next_to_buy_script.calculate_next_to_buy()
    next_purchases.calculate_next_purchases()

    print("Update complete.")

# Main entry point of the script
if __name__ == '__main__':
    asyncio.run(refresh_prices())