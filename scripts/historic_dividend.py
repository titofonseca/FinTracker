import aiohttp
import asyncio
import os
import sqlite3
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API and Database settings
DIVIDEND_API_URL = 'https://api.polygon.io/v3/reference/dividends'
API_KEY = os.getenv('API_KEY')
DATABASE_PATH = "db/database.db"  # Path to the database
TIMEOUT = 20  # API request timeout

async def get_final_reits():
    """
    Fetches a list of REIT tickers from the database.
    Returns a list of tickers.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT ticker FROM final_ticker_list')
    final_reits = [row[0] for row in cursor.fetchall()]
    conn.close()
    logging.info(f"Retrieved {len(final_reits)} REITs from the database.")
    return final_reits

async def fetch_dividend_data(session, ticker):
    """
    Fetches dividend data from the API for a given ticker.
    Returns a list of dividend data.
    """
    params = {'apiKey': API_KEY, 'ticker': ticker, 'limit': 50}  # Adjust limit as needed
    async with session.get(DIVIDEND_API_URL, params=params, timeout=TIMEOUT) as response:
        response.raise_for_status()
        data = await response.json()
        return data['results'] if 'results' in data else []

async def save_dividend_data(ticker, dividends):
    """
    Saves dividend data to the database for a given ticker.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    for dividend in dividends:
        cursor.execute('''
            INSERT INTO historic_dividends (ticker, data, record_date, ex_dividend_date, pay_date, dividend_amount) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ticker, 
            dividend.get('declaration_date', ''),  # Use empty string if declaration_date is not available
            dividend.get('record_date', ''),
            dividend.get('ex_dividend_date', ''),
            dividend.get('pay_date', ''),
            dividend.get('cash_amount', 0)  # Use 0 if cash_amount is not available
        ))
    conn.commit()
    conn.close()

async def process_ticker(session, ticker):
    """
    Processes a single ticker to fetch and save dividend data.
    Returns a tuple (ticker, success_flag).
    """
    try:
        dividend_data = await fetch_dividend_data(session, ticker)
        await save_dividend_data(ticker, dividend_data)
        return (ticker, True)
    except Exception as e:
        logging.error(f"Error processing dividend data for ticker {ticker}: {e}")
        return (ticker, False)

async def main():
    """
    Main function to initiate the dividend data retrieval process for all tickers.
    """
    logging.info("Starting the dividend data retrieval process.")
    etoro_reits = await get_final_reits()

    async with aiohttp.ClientSession() as session:
        tasks = [process_ticker(session, ticker) for ticker in etoro_reits]
        results = await asyncio.gather(*tasks)

    successful_tickers = [result[0] for result in results if result[1]]
    failed_tickers = [result[0] for result in results if not result[1]]

    logging.info(f"Dividend data retrieval completed. Success for {len(successful_tickers)} tickers.")
    if failed_tickers:
        logging.warning(f"Failed to retrieve dividend data for {len(failed_tickers)} tickers.")
        
if __name__ == '__main__':
    asyncio.run(main())
