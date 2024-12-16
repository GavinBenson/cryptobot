import os
import time
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Constants
DOWNLOAD_PATH = r'C:\Users\Mohammad Bin Salman\Downloads'
DB_PATH = 'crypto_data.db'
CRYPTO_DF = pd.DataFrame({
    'Name': ['Bitcoin', 'Ethereum', 'Ripple', 'Tether', 'Solana', 'Binance-Coin', 'Dogecoin', 'USD-Coin', 'Cardano', 'TRON'],
    'Ticker': ['BTC', 'ETH', 'XRP', 'USDT', 'SOL', 'BNB', 'DOGE', 'USDC', 'ADA', 'TRX']
})
TICKER_COLORS = {
    'BTC': Fore.YELLOW, 'ETH': Fore.CYAN, 'XRP': Fore.BLUE,
    'USDT': Fore.GREEN, 'SOL': Fore.MAGENTA, 'BNB': Fore.LIGHTYELLOW_EX,
    'DOGE': Fore.WHITE, 'USDC': Fore.LIGHTCYAN_EX, 'ADA': Fore.LIGHTGREEN_EX, 'TRX': Fore.RED
}

# Utility Functions
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_crypto_options(exclude_ticker=None):
    for _, row in CRYPTO_DF.iterrows():
        ticker = row['Ticker']
        if ticker != exclude_ticker:
            color = TICKER_COLORS.get(ticker, Fore.WHITE)
            print(f"{color}{row['Name']} ({ticker}){Style.RESET_ALL}")

def select_crypto(prompt="Select a cryptocurrency to plot:"):
    clear_console()
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    print(Fore.YELLOW + prompt + Style.RESET_ALL)
    display_crypto_options()
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    return input("Enter the ticker: ").strip().upper()

def crypto_name_from_ticker(ticker):
    return CRYPTO_DF[CRYPTO_DF['Ticker'] == ticker]['Name'].values[0]

def create_table_if_not_exists(ticker):
    print(f"[DEBUG] Ensuring table for {ticker} exists...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {ticker} (
        Date TEXT NOT NULL,
        Price REAL NOT NULL
    )
    """
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()
    print(f"[DEBUG] Table for {ticker} verified/created.")

def is_data_up_to_date(ticker):
    print(f"[DEBUG] Checking if data for {ticker} is up-to-date...")
    create_table_if_not_exists(ticker)  # Ensure table exists
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT Date FROM {ticker} ORDER BY Date DESC LIMIT 1"
        result = pd.read_sql_query(query, conn)
        conn.close()
        print(f"[DEBUG] Query result for {ticker}: {result}")
        if not result.empty:
            last_date = pd.to_datetime(result.iloc[0]['Date']).date()
            today = datetime.now().date()
            buffer_date = today - timedelta(days=2)
            print(f"[DEBUG] Last date in database for {ticker}: {last_date}")
            print(f"[DEBUG] Buffer date (today - 2 days): {buffer_date}")
            return last_date >= buffer_date
    except sqlite3.OperationalError as e:
        print(f"[DEBUG] OperationalError for {ticker}: {e}")
        return False
    print(f"[DEBUG] No data found for {ticker}.")
    return False

def download_crypto_data(ticker):
    print(f"[DEBUG] Starting download for {ticker}...")
    driver = webdriver.Firefox()
    try:
        crypto_name = crypto_name_from_ticker(ticker).lower()
        url = f"https://coincodex.com/crypto/{crypto_name}/historical-data/"
        driver.get(url)
        print(f"[DEBUG] Navigated to {url}")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "date-select"))
        ).click()
        print("[DEBUG] Date range selector clicked.")

        date_inputs = driver.find_elements(By.XPATH, "//input[@type='date']")
        if date_inputs:
            print("[DEBUG] Found date input fields.")
            date_inputs[0].send_keys("2010-12-12")

        submit_button = driver.find_element(By.XPATH, "//div[@class='dates-select']//button[@class='button button-primary']")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
        time.sleep(1)
        submit_button.click()
        print("[DEBUG] Submit button clicked.")

        time.sleep(3)
        driver.find_element(By.CLASS_NAME, "export").click()
        print("[DEBUG] Export button clicked.")
        time.sleep(2)
    finally:
        driver.quit()
        print("[DEBUG] Download complete. Browser closed.")

def load_latest_csv(download_path, crypto_name):
    print(f"[DEBUG] Loading latest CSV for {crypto_name} from {download_path}...")
    csv_files = [f for f in os.listdir(download_path) if f.endswith(".csv")]
    matching_files = [f for f in csv_files if crypto_name.lower() in f.lower()]
    print(f"[DEBUG] Found matching CSV files: {matching_files}")
    if not matching_files:
        raise FileNotFoundError(f"No CSV file found for {crypto_name} in {download_path}")
    latest_file = max(matching_files, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
    print(f"[DEBUG] Latest file selected: {latest_file}")
    return pd.read_csv(os.path.join(download_path, latest_file))

def clean_crypto_data(df):
    print("[DEBUG] Cleaning crypto data...")
    df.rename(columns={df.columns[0]: 'Date', df.columns[5]: 'Price'}, inplace=True)
    df['Price'] = df['Price'].replace(r'[^0-9.]', '', regex=True).astype(float)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    cleaned_df = df.dropna(subset=['Date', 'Price'])
    print(f"[DEBUG] Cleaned data: {cleaned_df.head()}")
    return cleaned_df

def save_to_database(df, ticker):
    print(f"[DEBUG] Saving data for {ticker} to database...")
    create_table_if_not_exists(ticker)  # Ensure table exists
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(ticker, conn, if_exists='replace', index=False)
    conn.close()
    print(f"[DEBUG] Data for {ticker} saved.")

def load_from_database(ticker, start_date=None, end_date=None):
    print(f"[DEBUG] Loading data for {ticker} from database...")
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM {ticker}"
    if start_date and end_date:
        query += f" WHERE Date BETWEEN '{start_date}' AND '{end_date}'"
    df = pd.read_sql_query(query, conn, parse_dates=['Date'])
    conn.close()
    print(f"[DEBUG] Loaded data for {ticker}: {df.head()}")
    return df

def plot_crypto_data(df1, name1, df2=None, name2=None):
    print(f"[DEBUG] Plotting data for {name1} (and {name2} if provided)...")
    fig = px.line(df1, x="Date", y="Price", title=f"{name1} Price Over Time", markers=True)
    if df2 is not None:
        fig.add_scatter(x=df2["Date"], y=df2["Price"], mode="lines+markers", name=name2)
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=True,
        template="plotly_dark",
    )
    fig.show()

# Main Logic
if __name__ == "__main__":
    while True:
        clear_console()
        choice = input("Would you like to plot (1) One or (2) Two cryptocurrencies? ").strip()
        first_ticker = select_crypto()

        if not is_data_up_to_date(first_ticker):
            print(f"[DEBUG] Data for {first_ticker} is outdated or missing. Downloading new data...")
            download_crypto_data(first_ticker)
            raw_data = load_latest_csv(DOWNLOAD_PATH, crypto_name_from_ticker(first_ticker))
            cleaned_data = clean_crypto_data(raw_data)
            save_to_database(cleaned_data, first_ticker)
        else:
            print(f"[DEBUG] Data for {first_ticker} is up-to-date. Skipping download.")

        data1 = load_from_database(first_ticker)
        name1 = crypto_name_from_ticker(first_ticker)

        if choice == '2':
            second_ticker = select_crypto(f"Select a second cryptocurrency (excluding {first_ticker}):")
            if not is_data_up_to_date(second_ticker):
                print(f"[DEBUG] Data for {second_ticker} is outdated or missing. Downloading new data...")
                download_crypto_data(second_ticker)
                raw_data = load_latest_csv(DOWNLOAD_PATH, crypto_name_from_ticker(second_ticker))
                cleaned_data = clean_crypto_data(raw_data)
                save_to_database(cleaned_data, second_ticker)
            else:
                print(f"[DEBUG] Data for {second_ticker} is up-to-date. Skipping download.")

            data2 = load_from_database(second_ticker)
            name2 = crypto_name_from_ticker(second_ticker)
            plot_crypto_data(data1, name1, data2, name2)
        else:
            plot_crypto_data(data1, name1)

        restart = input("\nWould you like to analyze another cryptocurrency? (y/n): ").strip().lower()
        if restart != 'y':
            print(Fore.GREEN + "Thank you for using Cryptobot! Goodbye!" + Style.RESET_ALL)
            break
