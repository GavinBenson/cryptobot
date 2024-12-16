import os
import time
import sqlite3
import pandas as pd
import plotly.express as px
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Constants
download_path = r'C:\Users\Mohammad Bin Salman\Downloads'
db_path = 'crypto_data.db'
database_path = 'crypto_data.db'
cryptodf = pd.DataFrame({
    'Name': ['Bitcoin', 'Ethereum', 'Ripple', 'Tether', 'Solana', 'Binance-Coin', 'Dogecoin', 'USD-Coin', 'Cardano', 'TRON'],
    'Ticker': ['BTC', 'ETH', 'XRP', 'USDT', 'SOL', 'BNB', 'DOGE', 'USDC', 'ADA', 'TRX']
})

ticker_colors = {
    'BTC': Fore.YELLOW,
    'ETH': Fore.CYAN,
    'XRP': Fore.BLUE,
    'USDT': Fore.GREEN,
    'SOL': Fore.MAGENTA,
    'BNB': Fore.LIGHTYELLOW_EX,
    'DOGE': Fore.WHITE,
    'USDC': Fore.LIGHTCYAN_EX,
    'ADA': Fore.LIGHTGREEN_EX,
    'TRX': Fore.RED
}

start_date = ''
end_date = ''

# Utility functions
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def select_crypto():
    clear_console()
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    print(Fore.YELLOW + "Select a cryptocurrency to plot:" + Style.RESET_ALL)
    
    for _, row in cryptodf.iterrows():
        ticker = row['Ticker']
        color = ticker_colors.get(ticker, Fore.WHITE)
        print(f"{color}{row['Name']} ({ticker}){Style.RESET_ALL}")

    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    return input("Enter the ticker: ").strip().upper()


def download_csv(selected_crypto):
    driver = webdriver.Firefox()

    try:
        if selected_crypto in cryptodf['Ticker'].values:
            crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto]['Name'].values[0]
            url = f"https://coincodex.com/crypto/{crypto_name.lower()}/historical-data/"
            driver.get(url)
        else:
            print("Invalid ticker. Please restart and try again.")
            return

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "date-select"))
        ).click()

        date_inputs = driver.find_elements(By.XPATH, "//input[@type='date']")
        if date_inputs:
            date_inputs[0].send_keys("2010-12-12")

        submit_button = driver.find_element(By.XPATH, "//div[@class='dates-select']//button[@class='button button-primary']")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
        time.sleep(1)
        submit_button.click()

        time.sleep(3)
        driver.find_element(By.CLASS_NAME, "export").click()
        time.sleep(2)
    finally:
        driver.quit()


def load_latest_csv(download_path, crypto_name):
    csv_files = [f for f in os.listdir(download_path) if f.endswith(".csv")]
    matching_files = [f for f in csv_files if crypto_name.lower() in f.lower()]

    if not matching_files:
        raise FileNotFoundError(f"No CSV file found for {crypto_name} in {download_path}")

    latest_file = max(matching_files, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
    return pd.read_csv(os.path.join(download_path, latest_file))


def clean_crypto_data(df):
    df.rename(columns={df.columns[0]: 'Date', df.columns[5]: 'Price'}, inplace=True)
    df['Price'] = df['Price'].replace(r'[^0-9.]', '', regex=True).astype(float)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df.dropna(subset=['Date', 'Price'])


def save_to_database(df, crypto_name):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {crypto_name} (
        Date TEXT,
        Price REAL
    )
    ''')

    # Insert data
    df.to_sql(crypto_name, conn, if_exists='replace', index=False)

    # Debug statement: Verify rows
    cursor.execute(f'SELECT * FROM {crypto_name} LIMIT 5')
    rows = cursor.fetchall()
    print(Fore.CYAN + f"Debug: Sample data from {crypto_name} table:" + Style.RESET_ALL)
    for row in rows:
        print(row)

    # Close the connection
    conn.close()

def load_from_database(crypto_name, start_date=None, end_date=None):
    conn = sqlite3.connect(database_path)
    query = f"SELECT * FROM {crypto_name}"
    if start_date and end_date:
        query += f" WHERE Date BETWEEN '{start_date}' AND '{end_date}'"
    else:
        query += " ORDER BY Date ASC"  # Return all data if no date range is provided
    df = pd.read_sql_query(query, conn, parse_dates=['Date'])
    conn.close()
    return df

def filter_date_range(df):
    start_date = pd.to_datetime(input("Enter start date (YYYY-MM-DD): ").strip())
    end_date = pd.to_datetime(input("Enter end date (YYYY-MM-DD): ").strip())
    return df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]


def select_second_crypto(selected_crypto):
    """
    Allow the user to select a second cryptocurrency that is different from the first.
    """
    clear_console()
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    print(Fore.YELLOW + "Select a second cryptocurrency to plot:" + Style.RESET_ALL)
    
    for _, row in cryptodf.iterrows():
        ticker = row['Ticker']
        if ticker != selected_crypto:  # Exclude the first selected crypto
            color = ticker_colors.get(ticker, Fore.WHITE)
            print(f"{color}{row['Name']} ({ticker}){Style.RESET_ALL}")

    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    return input("Enter the ticker for the second cryptocurrency: ").strip().upper()


def plot_crypto_data(df1, crypto1_name, df2=None, crypto2_name=None):
    """
    Plot one or two cryptocurrencies on the same chart.
    """
    fig = px.line(
        df1,
        x="Date",
        y="Price",
        title=f"{crypto1_name} Price Over Time",
        labels={"Price": "Price (USD)", "Date": "Date"},
        markers=True
    )
    
    if df2 is not None and crypto2_name is not None:
        fig.add_scatter(
            x=df2["Date"],
            y=df2["Price"],
            mode="lines+markers",
            name=f"{crypto2_name} Price",
            line=dict(dash="dash")
        )
        fig.update_layout(title=f"{crypto1_name} and {crypto2_name} Prices Over Time")

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=True,
        template="plotly_dark",
        title_font_size=16
    )
    fig.show()


if __name__ == "__main__":
    # Step 1: Choose whether to plot 1 or 2 cryptocurrencies
    clear_console()
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    print(Fore.YELLOW + "How many cryptocurrencies would you like to plot?" + Style.RESET_ALL)
    print("1. One cryptocurrency")
    print("2. Two cryptocurrencies")
    print(Fore.GREEN + "=" * 80 + Style.RESET_ALL)
    choice = input("Enter your choice (1 or 2): ").strip()

    # First cryptocurrency selection
    selected_crypto = select_crypto()

    # Check and update data for the first cryptocurrency
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT Date FROM {selected_crypto} ORDER BY Date DESC LIMIT 1"
    try:
        cursor.execute(query)
        last_date = cursor.fetchone()
        conn.close()

        if last_date and pd.to_datetime(last_date[0]).date() == pd.Timestamp.today().date():
            print(Fore.GREEN + f"Data for {selected_crypto} is up to date in the database." + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "Downloading and updating data..." + Style.RESET_ALL)
            download_csv(selected_crypto)
            crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto]['Name'].values[0]
            raw_data = load_latest_csv(download_path, crypto_name)
            cleaned_data = clean_crypto_data(raw_data)
            save_to_database(cleaned_data, selected_crypto)

    except sqlite3.OperationalError:
        conn.close()
        print(Fore.RED + "No existing data found. Downloading new data..." + Style.RESET_ALL)
        download_csv(selected_crypto)
        crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto]['Name'].values[0]
        raw_data = load_latest_csv(download_path, crypto_name)
        cleaned_data = clean_crypto_data(raw_data)
        save_to_database(cleaned_data, selected_crypto)

    # Load data for the first cryptocurrency
    print(Fore.YELLOW + "Loading data from the database..." + Style.RESET_ALL)
    start_date_input = input("Enter start date (YYYY-MM-DD) or press Enter to use all data: ").strip()
    end_date_input = input("Enter end date (YYYY-MM-DD) or press Enter to use all data: ").strip()
    start_date = pd.to_datetime(start_date_input) if start_date_input else None
    end_date = pd.to_datetime(end_date_input) if end_date_input else None

    data_from_db1 = load_from_database(selected_crypto, start_date, end_date)
    crypto1_name = cryptodf[cryptodf['Ticker'] == selected_crypto]['Name'].values[0]

    # If user chose to plot two cryptocurrencies
    if choice == '2':
        # Second cryptocurrency selection
        selected_crypto2 = select_second_crypto(selected_crypto)

        # Check and update data for the second cryptocurrency
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT Date FROM {selected_crypto2} ORDER BY Date DESC LIMIT 1"
        try:
            cursor.execute(query)
            last_date = cursor.fetchone()
            conn.close()

            if last_date and pd.to_datetime(last_date[0]).date() == pd.Timestamp.today().date():
                print(Fore.GREEN + f"Data for {selected_crypto2} is up to date in the database." + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + "Downloading and updating data..." + Style.RESET_ALL)
                download_csv(selected_crypto2)
                crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto2]['Name'].values[0]
                raw_data = load_latest_csv(download_path, crypto_name)
                cleaned_data = clean_crypto_data(raw_data)
                save_to_database(cleaned_data, selected_crypto2)

        except sqlite3.OperationalError:
            conn.close()
            print(Fore.RED + "No existing data found. Downloading new data..." + Style.RESET_ALL)
            download_csv(selected_crypto2)
            crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto2]['Name'].values[0]
            raw_data = load_latest_csv(download_path, crypto_name)
            cleaned_data = clean_crypto_data(raw_data)
            save_to_database(cleaned_data, selected_crypto2)

        # Load data for the second cryptocurrency
        print(Fore.YELLOW + "Loading data from the database..." + Style.RESET_ALL)
        data_from_db2 = load_from_database(selected_crypto2, start_date, end_date)
        crypto2_name = cryptodf[cryptodf['Ticker'] == selected_crypto2]['Name'].values[0]

        # Plot both cryptocurrencies
        plot_crypto_data(data_from_db1, crypto1_name, data_from_db2, crypto2_name)

    else:
        # Plot only the first cryptocurrency
        plot_crypto_data(data_from_db1, crypto1_name)
        