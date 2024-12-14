from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from colorama import Fore, Back, Style, just_fix_windows_console
from colorama import init
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import plotly.express as px


init(convert=True)

cryptodf = pd.DataFrame()
cryptodf['Name'] = ['Bitcoin', 'Ethereum', 'Ripple', 'Tether', 'Solana', 'Binance-Coin', 'Dogecoin', 'USD-Coin', 'Cardano', 'TRON']
cryptodf['Ticker'] = ['BTC', 'ETH', 'XRP', 'USDT', 'SOL', 'BNB', 'DOGE', 'USDC', 'ADA', 'TRX']
download_path = r'C:\Users\Mohammad Bin Salman\Downloads'

ticker_colors = {
    'BTC': Fore.YELLOW,  # Bitcoin - Red
    'ETH': Fore.CYAN,  # Ethereum - Green
    'XRP': Fore.BLUE,  # Ripple - Blue
    'USDT': Fore.GREEN,  # Tether - Cyan
    'SOL': Fore.MAGENTA,  # Solana - Yellow
    'BNB': Fore.LIGHTYELLOW_EX,  # Binance Coin - Magenta
    'DOGE': Fore.WHITE,  # Dogecoin - White
    'USDC': Fore.LIGHTCYAN_EX,  # USD Coin - Light Cyan
    'ADA': Fore.LIGHTGREEN_EX,  # Cardano - Light Green
    'TRX': Fore.RED  # TRON - Light Yellow
}

clear = lambda: os.system('cls')


# Select crypto
def selectCrypto():
    clear()
    print(Fore.GREEN + "=" * 120 + Style.RESET_ALL)
    print(Fore.YELLOW + "What crypto would you like to plot data for?\n" + Style.RESET_ALL)
    
    # Display the available cryptocurrencies and their tickers with colors
    for _, row in cryptodf.iterrows():
        ticker = row['Ticker']
        color = ticker_colors.get(ticker, Fore.WHITE)  # Default to white if no color is found
        print(f"{color}{row['Name']} ({ticker}){Style.RESET_ALL}")
    print('\n')
    selected = input().upper()
    print(Fore.GREEN + "=" * 120 + Style.RESET_ALL)
    return selected

# Call selectCrypto to allow the user to select a cryptocurrency
selectedCrypto = selectCrypto()

def downloadCsv():
	    
    # Start WebDriver
    driver = webdriver.Firefox()

    # Check if selectedCrypto is in the 'Ticker' column
    if selectedCrypto in cryptodf['Ticker'].values:
       # Find the corresponding crypto name and format it for the URL
        crypto_name = cryptodf[cryptodf['Ticker'] == selectedCrypto]['Name'].values[0]
        driver.get(f"https://coincodex.com/crypto/{crypto_name.lower()}/historical-data/")
    else:
        print("Crypto not found. Please enter a valid ticker (BTC, ETH, XRP, DOGE, etc).")
    
    # Wait for the page to load
    time.sleep(1.5)

    # Click the date selector button
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "date-select"))
    )
    button.click()

    # Set the start date
    date_inputs = driver.find_elements(By.XPATH, "//input[@type='date']")
    if date_inputs:
        first_date_input = date_inputs[0]
        first_date_input.send_keys("2010-12-12")

    # Submit the date range
    submitButton = driver.find_element(By.XPATH, "//div[@class='dates-select']//button[@class='button button-primary']")
    driver.execute_script("arguments[0].scrollIntoView(true);", submitButton)
    time.sleep(1)
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submitButton)
    time.sleep(1)
    submitButton.click()

    # Select Monthly Frequency
   # dropdown = driver.find_element(By.CLASS_NAME, "custom-native-select")
    #dropdown.click()
   # time.sleep(1)
   # monthly_option = driver.find_element(By.XPATH, "//div[@class='item' and contains(text(), 'Frequency Monthly')]")
   # monthly_option.click()
    time.sleep(5)
    # Click Export button to download the CSV
    exportBtn = driver.find_element(By.CLASS_NAME, "export")
    exportBtn.click()

    # Wait for the CSV file to download
    time.sleep(2)


    # Close the browser
    driver.quit()

downloadCsv()
time.sleep(1)
clear()
print('Loading data...')



def load_latest_csv(download_path, crypto_name):
    # Find all CSV files in the directory
    csv_files = [f for f in os.listdir(download_path) if f.endswith(".csv")]
    
    # Filter files containing the crypto ticker in their names (case-insensitive)
    matching_files = [f for f in csv_files if crypto_name.lower() in f.lower()]
    
    if not matching_files:
        raise FileNotFoundError(f"No CSV file found for {crypto_name} in {download_path}")
    
    # Get the most recently modified file
    latest_file = max(matching_files, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
    
    # Full path to the CSV file
    latest_file_path = os.path.join(download_path, latest_file)
    
    print(f"Loading CSV: {latest_file_path}")
    return pd.read_csv(latest_file_path)

# Example usage
download_path = r'C:\Users\Mohammad Bin Salman\Downloads'
crypto_name = cryptodf[cryptodf['Ticker'] == selectedCrypto]['Name'].values[0]
crypto_data = load_latest_csv(download_path, crypto_name)

# Clean the data
crypto_data.rename(columns={crypto_data.columns[0]: 'Date', crypto_data.columns[5]: 'Price'}, inplace=True)
crypto_data['Price'] = crypto_data['Price'].replace(r'[^0-9.]', '', regex=True)  # Remove non-numeric characters
crypto_data['Price'] = pd.to_numeric(crypto_data['Price'], errors='coerce')  # Convert to numeric, handle errors by coercing
crypto_data['Date'] = pd.to_datetime(crypto_data['Date'], errors='coerce')  # Convert to datetime format
crypto_data.dropna(subset=['Date', 'Price'], inplace=True)  # Drop rows with missing values

# Define date range
print('What date range (YYYY-MM-DD) \n From: ')
start_date = input()
print('To: ')
end_date = input()

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

date_filtered_data = crypto_data[(crypto_data['Date'] >= start_date) & (crypto_data['Date'] <= end_date)]

# Plot the data using Plotly
fig = px.line(date_filtered_data, 
              x="Date", 
              y="Price", 
              title=f'{crypto_name} Price Over Time',
              labels={'Price': 'Price (USD)', 'Date': 'Date'},
              markers=True)

# Customize layout
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    xaxis_rangeslider_visible=True,  # Adds range slider for zooming
    template="plotly_dark",  # Change the theme to 'plotly_dark' or any other theme
    title_font_size=16,
)

# Show the interactive plot
fig.show()

