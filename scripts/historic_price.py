import aiohttp
import asyncio
import os
import datetime
import sqlite3
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API and Database settings
API_BASE_URL = os.getenv('API_BASE_URL2', 'https://api.polygon.io/v2/aggs/ticker')
API_KEY = os.getenv('API_KEY')
TIMEFRAME = 'day'
MULTIPLIER = 1
TIMEOUT = 20
DATABASE_PATH = "db/database.db"  # Update with your database path

async def get_final_reits():
    """Fetches a list of REITs from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT ticker FROM final_ticker_list')
    final_reits = [row[0] for row in cursor.fetchall()]
    conn.close()
    logging.info(f"Retrieved {len(final_reits)} REITs from the database.")
    return final_reits

async def fetch_stock_data(session, ticker, from_date, to_date):
    """Fetches stock data from the API."""
    url = f"{API_BASE_URL}/{ticker}/range/{MULTIPLIER}/{TIMEFRAME}/{from_date}/{to_date}"
    params = {'apiKey': API_KEY, 'adjusted': 'true', 'sort': 'asc'}
    async with session.get(url, params=params, timeout=TIMEOUT) as response:
        response.raise_for_status()
        data = await response.json()
        return data['results'] if 'results' in data else []

async def save_stock_data(ticker, data):
    """Saves stock data to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    for entry in data:
        date = datetime.datetime.fromtimestamp(entry['t'] / 1000).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO historic_price (ticker, data, close_price, open_price, highest_price, lowest_price) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticker, date, entry['c'], entry['o'], entry['h'], entry['l']))
    conn.commit()
    conn.close()

async def process_ticker(session, ticker, from_date, to_date):
    """Processes a single ticker."""
    try:
        stock_data = await fetch_stock_data(session, ticker, from_date, to_date)
        await save_stock_data(ticker, stock_data)
        return (ticker, True)
    except Exception as e:
        logging.error(f"Error processing ticker {ticker}: {e}")
        return (ticker, False)

async def main():
    """Main function to process all tickers."""
    logging.info("Starting the stock data retrieval process.")
    etoro_reits = await get_final_reits()
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=365)  # Fetching data for the past year
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    async with aiohttp.ClientSession() as session:
        tasks = [process_ticker(session, ticker, start_date_str, end_date_str) for ticker in etoro_reits]
        results = await asyncio.gather(*tasks)

    successful_tickers = [result[0] for result in results if result[1]]
    failed_tickers = [result[0] for result in results if not result[1]]

    logging.info(f"Data retrieval completed. Success for {len(successful_tickers)} tickers.")
    if failed_tickers:
        logging.info(f"Failed to retrieve data for {len(failed_tickers)} tickers.")
        
if __name__ == '__main__':
    asyncio.run(main())
