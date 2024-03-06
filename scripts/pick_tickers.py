import asyncio
import aiohttp
import datetime
import sqlite3
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def get_db_connection():
    """
    Establishes and returns a connection to the database.
    """
    return sqlite3.connect('db/database.db')

async def fetch_etoro_reits(session):
    """
    Asynchronously fetches REITs from eToro API.
    Args:
        session (aiohttp.ClientSession): The HTTP client session.
    Returns:
        list: A list of REIT symbols.
    """
    logging.info("Fetching REITs from eToro...")
    API_ETORO_URL = 'https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments/bulk?bulkNumber=1&totalBulks=1'
    response = await session.get(API_ETORO_URL)
    response.raise_for_status()
    data = await response.json()
    return [d['SymbolFull'] for d in data['InstrumentDisplayDatas'] if not d['IsInternalInstrument']]

async def fetch_recent_price(session, ticker):
    """
    Asynchronously fetches the most recent price of a ticker.
    Args:
        session (aiohttp.ClientSession): The HTTP client session.
        ticker (str): The ticker symbol.
    Returns:
        tuple: A tuple containing the date and the price.
    """
    API_BASE_URL = 'https://api.polygon.io/v2/aggs/ticker'
    API_KEY = os.getenv('API_KEY')
    TIMEFRAME = 'second'
    MULTIPLIER = 1

    now = datetime.datetime.now()
    from_date = (now - datetime.timedelta(days=4)).strftime('%Y-%m-%d')
    to_date = now.strftime('%Y-%m-%d')

    url = f"{API_BASE_URL}/{ticker}/range/{MULTIPLIER}/{TIMEFRAME}/{from_date}/{to_date}?adjusted=true&sort=asc&apiKey={API_KEY}"

    try:
        response = await session.get(url)
        if response.status == 403:
            logging.warning(f"Access forbidden for {ticker}")
            return None, None

        data = await response.json()
        results = data.get('results', [])

        if results:
            latest_result = results[-1]
            date = datetime.datetime.fromtimestamp(latest_result['t'] / 1000).strftime('%Y-%m-%d %H:%M')
            return date, latest_result['c']
    except Exception as e:
        logging.error(f"Error fetching price data for {ticker}: {e}")

    return None, None

# Function to fetch the last dividend paid or announced for a ticker
async def fetch_recent_dividend(session, ticker):
    """
    Asynchronously fetches the last dividend paid or announced for a ticker.
    Args:
        session (aiohttp.ClientSession): The HTTP client session.
        ticker (str): The ticker symbol.
    Returns:
        tuple: A tuple containing the dividend payout date and amount.
    """
    API_BASE_URL = 'https://api.polygon.io/v3/reference/dividends'
    API_KEY = os.getenv('API_KEY')

    params = {
        'apiKey': API_KEY,
        'ticker': ticker,
        'limit': 1
    }

    try:
        response = await session.get(API_BASE_URL, params=params)
        if response.status == 403:
            logging.warning(f"Access forbidden for {ticker}")
            return None, None

        data = await response.json()
        results = data.get('results', [])

        if results:
            dividend = results[0]
            payout_date = dividend.get('pay_date', None)
            amount = dividend.get('cash_amount', None)
            return payout_date, amount
    except Exception as e:
        logging.error(f"Error fetching dividend data for {ticker}: {e}")

    return None, None

# Function to clear the 'all_etoro_data' table in the database
def clear_all_etoro_data_table():
    """
    Clears the 'all_etoro_data' table in the database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='all_etoro_data';")
        if cursor.fetchone():
            cursor.execute('DELETE FROM all_etoro_data')
            conn.commit()
        else:
            print("Table 'all_etoro_data' does not exist.")
    finally:
        conn.close()

# Function to save price and dividend data to the 'all_etoro_data' table
def save_etoro_data(ticker, recent_price, price_date, recent_dividend, dividend_date):
    """
    Saves the fetched data for a ticker into the 'all_etoro_data' table in the database.
    Args:
        ticker (str): Stock ticker symbol.
        recent_price (float): The most recent price of the stock.
        price_date (str): Date of the recent price.
        recent_dividend (float): The most recent dividend amount.
        dividend_date (str): Date of the recent dividend.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO all_etoro_data 
                          (ticker, recent_price, price_date, recent_dividend, dividend_date) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (ticker, recent_price, price_date, recent_dividend, dividend_date))
        conn.commit()
    finally:
        conn.close()

# Function to create the 'final_ticker_list' table in the database
def create_final_ticker_list_table():
    """
    Creates the 'final_ticker_list' table in the database if it doesn't exist.
    """
    conn = get_db_connection()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS final_ticker_list (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ticker TEXT UNIQUE
                        )''')
        conn.commit()
    finally:
        conn.close()

# Function to insert ticker into the 'final_ticker_list' table
def insert_into_final_ticker_list(ticker):
    """
    Inserts a ticker into the 'final_ticker_list' table in the database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM final_ticker_list WHERE ticker = ?', (ticker,))
        data = cursor.fetchone()
        if data is None:
            cursor.execute('INSERT INTO final_ticker_list (ticker) VALUES (?)', (ticker,))
            conn.commit()
    finally:
        conn.close()

# Function to get combined REITs
# Updated function to get combined REITs
def get_combined_reits(etoro_reits, scraped_reits):
    global total_etoro_reits, total_scraped_reits, total_env_reits, total_db_reits, total_combined_reits
    logging.info("Combining REITs from various sources...")
    conn = get_db_connection()
    cursor = conn.cursor()

    reits_to_watch = set(os.getenv('REITS_TO_WATCH', '').split(','))
    total_env_reits = len(reits_to_watch)

    cursor.execute('SELECT DISTINCT ticker FROM reit')
    reits_from_db = set(row[0] for row in cursor.fetchall())
    total_db_reits = len(reits_from_db)

    total_etoro_reits = len(etoro_reits)
    total_scraped_reits = len(scraped_reits)

    combined_reits = set(etoro_reits).union(scraped_reits).union(reits_to_watch).union(reits_from_db)
    total_combined_reits = len(combined_reits)

    conn.close()
    return combined_reits

# Funções para scraping adicionadas aqui
def safe_find_element_by_css(row, selector):
    try:
        return row.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return None

def scrape_table_data(driver):
    table_data = []
    rows = driver.find_elements(By.CLASS_NAME, 'mp-table-body-row')
    for row in rows:
        cell_text = safe_find_element_by_css(row, '.t-order-1')
        if cell_text:
            ticker_match = re.search(r'([A-Z0-9]+) \| [^\|]+\|', cell_text)
            if ticker_match:
                table_data.append(ticker_match.group(1))
    return table_data

def scrape_for_reits():
    """
    Performs web scraping to obtain additional REITs.
    """
    logging.info("Starting web scraping for additional REITs...")
    chromedriver_path = '/Users/titofonseca/Downloads/chromedriver-mac-arm64/chromedriver'
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.dividend.com/")
        logging.info("Dividend.com page loaded successfully.")

        # Clicking sort button to order the data
        sort_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-column-key='Name']")))
        sort_button.click()
        time.sleep(3)
        sort_button.click()
        time.sleep(3)

        filters = ["Stocks", "ETFs", "Active ETFs", "Funds"]
        all_tickers = []

        # Applying different filters and scraping data
        for filter_name in filters:
            logging.info(f"Applying filter: {filter_name}")
            for attempt in range(5):
                try:
                    filter_element = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{filter_name}')]")))
                    filter_element.click()
                    time.sleep(3)
                    break
                except TimeoutException:
                    if attempt == 4:
                        continue

            while True:
                try:
                    scraped_data = scrape_table_data(driver)
                    all_tickers.extend(scraped_data)

                    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".mp-table-pagination-button[data-action='click->table-pagination#nextPage']")))
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)
                except (NoSuchElementException, TimeoutException):
                    break
                except StaleElementReferenceException:
                    time.sleep(3)

    finally:
        driver.quit()

    return list(set(all_tickers))  # Return unique tickers

# Variables for counting
total_etoro_reits = 0
total_scraped_reits = 0
total_env_reits = 0
total_db_reits = 0
total_combined_reits = 0

async def main():
    """
    Main function for fetching and updating REIT data.
    """
    logging.info("Starting REIT data update process")
    await async_main()
    logging.info("Completed REIT data update process")

# Async main function
async def async_main():
    """
    Async main function to fetch recent prices and dividends for REITs.
    """
    clear_all_etoro_data_table()
    create_final_ticker_list_table()

    async with aiohttp.ClientSession() as session:
        etoro_reits = await fetch_etoro_reits(session)
        scraped_reits = scrape_for_reits()  # Ensure this is called before using it
        combined_reits = get_combined_reits(etoro_reits, scraped_reits)

        tasks = []
        for ticker in combined_reits:
            tasks.append(fetch_recent_price(session, ticker))
            tasks.append(fetch_recent_dividend(session, ticker))

        results = await asyncio.gather(*tasks)

        for i in range(0, len(results), 2):
            ticker = list(combined_reits)[i // 2]
            price_date, recent_price = results[i]
            dividend_date, recent_dividend = results[i + 1]

            if recent_price is not None and recent_dividend is not None:
                insert_into_final_ticker_list(ticker)

            save_etoro_data(ticker, recent_price, price_date, recent_dividend, dividend_date)

if __name__ == '__main__':
    asyncio.run(main())
    logging.info(f"Total eToro REITs: {total_etoro_reits}")
    logging.info(f"Total Scraped REITs: {total_scraped_reits}")
    logging.info(f"Total REITs from Environmental Variables: {total_env_reits}")
    logging.info(f"Total REITs from Database: {total_db_reits}")
    logging.info(f"Total Combined REITs: {total_combined_reits}")


