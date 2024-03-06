# Import custom scripts
from scripts import reit_info, recent_price, historic_price, historic_dividend
import scripts.pick_tickers as pick_tickers
import scripts.latest_data as latest_data_script
import scripts.total_portfolio as total_portfolio_script
import scripts.hold_or_sell as hold_or_sell_script
import scripts.recovery_metrics as recovery_metrics_script
import scripts.next_to_buy as next_to_buy_script
import scripts.next_purchases as next_purchases
import logging
import asyncio

async def refresh_all_database():
    """
    Main function to refresh all database tables.
    This function coordinates the update process of various components in the system.
    """

    logging.info("Starting database update process")

    # Call the pick_tickers first (uncomment if needed)
    await pick_tickers.main()

    # Update each section of the database
    await update_section(reit_info.main, "REIT information")
    await update_section(recent_price.main, "Recent price")
    await update_section(historic_price.main, "Historic price")
    await update_section(historic_dividend.main, "Historic dividend")

    # Update data in synchronous functions
    update_sync_section(latest_data_script.update_latest_data, "Latest data")
    update_sync_section(total_portfolio_script.calculate_and_insert_portfolio_data, "Total portfolio data")
    update_sync_section(hold_or_sell_script.update_hold_or_sell_table, "Hold or sell table")
    update_sync_section(next_to_buy_script.calculate_next_to_buy, "Next to buy")
    update_sync_section(next_purchases.calculate_next_purchases, "Next purchases")

    logging.info("Database update process complete.")

async def update_section(update_func, section_name):
    """
    Helper function to update a specific section of the database.
    Logs the start and end of the update process for each section.

    Args:
    update_func (function): The asynchronous function to run for updating the section.
    section_name (str): Name of the section being updated.
    """
    logging.info(f"Starting update of {section_name}")
    await update_func()
    logging.info(f"Completed update of {section_name}")

def update_sync_section(update_func, section_name):
    """
    Helper function to update a specific section of the database using a synchronous function.
    Logs the start and end of the update process.

    Args:
    update_func (function): The synchronous function to run for updating the section.
    section_name (str): Name of the section being updated.
    """
    logging.info(f"Starting update of {section_name}")
    update_func()
    logging.info(f"Completed update of {section_name}")

# Main entry point of the script
if __name__ == '__main__':
    asyncio.run(refresh_all_database())
