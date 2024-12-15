import os
import time
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

        time.sleep(5)
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

def filter_date_range(df):
    start_date = pd.to_datetime(input("Enter start date (YYYY-MM-DD): ").strip())
    end_date = pd.to_datetime(input("Enter end date (YYYY-MM-DD): ").strip())
    return df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

def plot_crypto_data(df, crypto_name):
    fig = px.line(
        df,
        x="Date",
        y="Price",
        title=f"{crypto_name} Price Over Time",
        labels={"Price": "Price (USD)", "Date": "Date"},
        markers=True
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=True,
        template="plotly_dark",
        title_font_size=16
    )
    fig.show()

# Main script
if __name__ == "__main__":
    selected_crypto = select_crypto()
    download_csv(selected_crypto)

    crypto_name = cryptodf[cryptodf['Ticker'] == selected_crypto]['Name'].values[0]
    raw_data = load_latest_csv(download_path, crypto_name)
    cleaned_data = clean_crypto_data(raw_data)
    filtered_data = filter_date_range(cleaned_data)
    plot_crypto_data(filtered_data, crypto_name)
