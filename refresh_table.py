import os
import sys
import asyncio

# Adicionando o diretório de scripts ao path para importar os módulos
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

import scripts.available_reits as available_reits
from scripts import reit_info
from scripts import recent_price
from scripts import historic_price
from scripts import historic_dividend
import scripts.latest_data as latest_data_script
import scripts.total_portfolio as total_portfolio_script
import scripts.hold_or_sell as hold_or_sell_script
import scripts.recovery_metrics as recovery_metrics_script
import scripts.next_to_buy as next_to_buy_script
import scripts.scrap_and_clean_list as scrap_and_clean_list
import scripts.next_purchases as next_purchases


async def refresh_all_tables():
    # Atualizar preços recentes
    print("Atualizando preços recentes...")
    await reit_info.main()  # chamada assíncrona para recent_price.main()
    # await next_to_buy_script.calculate_next_to_buy()  # exemplo de outra chamada assíncrona, se necessário
    #next_purchases.calculate_next_purchases()

    print("Atualização completa.")

if __name__ == '__main__':
    asyncio.run(refresh_all_tables())
