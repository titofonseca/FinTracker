import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv
import aiosqlite

# Load environment variables from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API configuration
API_BASE_URL = os.getenv('API_BASE_URL3', 'https://api.polygon.io/v3/reference/tickers')
API_KEY = os.getenv('API_KEY')

async def add_api_key_to_url_async(url):
    """
    Appends the API key to the URL if the URL is not None.
    Returns the modified URL.
    """
    return f"{url}?apiKey={API_KEY}" if url else url

async def get_final_reits():
    """
    Retrieves a list of REITs marked as available on eToro from the database.
    Returns a list of REIT tickers.
    """
    async with aiosqlite.connect('db/database.db') as conn:
        logging.info("Retrieving REITs from final_ticker_list.")
        cursor = await conn.execute('SELECT ticker FROM final_ticker_list')
        final_reits = [row[0] for row in await cursor.fetchall()]
        logging.info(f"Retrieved {len(final_reits)} REITs.")
        return final_reits

async def fetch_reit_info(session, ticker):
    """
    Fetches detailed information of a given REIT from the API.
    Returns the REIT information or None if not found.
    """
    url = f"{API_BASE_URL}/{ticker}?apiKey={API_KEY}"
    async with session.get(url) as response:
        if response.status == 404:
            logging.warning(f"No data found for {ticker}.")
            return None
        response.raise_for_status()
        data = await response.json()  # Wait for the response data
        return data.get('results')

async def main():
    """
    Main function to update information of REITs.
    """
    logging.info("Starting REIT information update process...")
    final_reits = await get_final_reits()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_reit_info(session, ticker) for ticker in final_reits]
        results = await asyncio.gather(*tasks)

        for ticker, info in zip(final_reits, results):
            if info:
                branding = info.get('branding', {})
                logo_url = await add_api_key_to_url_async(branding.get('logo_url'))
                icon_url = await add_api_key_to_url_async(branding.get('icon_url'))

                # Update the database with the fetched information
                async with aiosqlite.connect('db/database.db') as conn:
                    await conn.execute('PRAGMA foreign_keys=ON;')
                    await conn.execute('''CREATE TABLE IF NOT EXISTS reit_info (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            ticker TEXT UNIQUE,
                                            name TEXT,
                                            homepage_url TEXT,
                                            logo_url TEXT,
                                            icon_url TEXT
                                        )''')
                    await conn.commit()

                    await conn.execute('''INSERT OR REPLACE INTO reit_info 
                                          (ticker, name, homepage_url, logo_url, icon_url) 
                                          VALUES (?, ?, ?, ?, ?)''',
                                      (ticker,
                                       info['name'],
                                       info.get('homepage_url', 'N/A'),
                                       logo_url if logo_url != 'N/A' else None,
                                       icon_url if icon_url != 'N/A' else None))
                    await conn.commit()

    logging.info("REIT information update process completed.")

if __name__ == '__main__':
    asyncio.run(main())
