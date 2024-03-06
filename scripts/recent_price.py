import aiohttp
import asyncio
import datetime
import sqlite3
from db import database
import os
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API and Database settings
API_BASE_URL = 'https://api.polygon.io/v2/aggs/ticker'
API_KEY = os.getenv('API_KEY')
TIMEFRAME = 'second'
MULTIPLIER = 1

def get_final_reits():
    """
    Retrieves a list of REITs from the database.
    Returns a list of REIT tickers.
    """
    conn = sqlite3.connect('db/database.db')
    logging.info("Retrieving REITs from final_ticker_list.")
    cursor = conn.execute('SELECT ticker FROM final_ticker_list')
    all_reits = [row[0] for row in cursor.fetchall()]
    conn.close()
    logging.info(f"Retrieved {len(all_reits)} REITs.")
    return all_reits

async def fetch_recent_price(session, ticker):
    """
    Fetches recent price information for a given REIT ticker.
    Returns the most recent date and price or None if unavailable.
    """
    now = datetime.datetime.now()
    from_date = (now - datetime.timedelta(days=4)).strftime('%Y-%m-%d')
    to_date = now.strftime('%Y-%m-%d')
    url = f"{API_BASE_URL}/{ticker}/range/{MULTIPLIER}/{TIMEFRAME}/{from_date}/{to_date}?adjusted=true&sort=asc&apiKey={API_KEY}"
    
    async with session.get(url) as response:
        if response.status == 403:
            logging.warning(f"Access forbidden for ticker {ticker}.")
            return None, None

        try:
            response.raise_for_status()
            data = await response.json()
            results = data.get('results', [])

            # Handling pagination if necessary
            next_url = data.get('next_url')
            while next_url:
                next_url_with_key = f"{next_url}&apiKey={API_KEY}"
                async with session.get(next_url_with_key) as next_response:
                    next_response.raise_for_status()
                    next_data = await next_response.json()
                    results.extend(next_data.get('results', []))
                    next_url = next_data.get('next_url')

            # Extract the most recent price
            if results:
                latest_result = results[-1]
                date = datetime.datetime.fromtimestamp(latest_result['t'] / 1000).strftime('%Y-%m-%d %H:%M')
                return date, latest_result['c']
            return None, None
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return None, None

async def main():
    """
    Main function to update the most recent price for each REIT.
    """
    logging.info("Starting the process to update recent prices for REITs.")
    final_reits = get_final_reits()
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_recent_price(session, ticker) for ticker in final_reits]
        results = await asyncio.gather(*tasks)

        for ticker, (date, price) in zip(final_reits, results):
            if date and price:
                # Update the database with the most recent price
                database.add_or_update_recent_price(ticker, date, price)

if __name__ == '__main__':
    asyncio.run(main())
