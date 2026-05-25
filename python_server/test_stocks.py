import sys
import os
import logging

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Adjust python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_server.shared.service.stock_market_service import get_daily_price_change

def test_stocks():
    tickers = ["GOOG", "BTC-USD", "^GSPC", "EXV3.DE"]
    print("==================================================")
    print("Testing Live Tickers Fetching via yfinance...")
    print("==================================================")
    
    # We clear the cache file if it exists to force a live network request
    cache_path = "/var/weather/stock_data_cache.json"
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            print("Cleared stock data cache to force live fetch.")
        except Exception as e:
            print(f"Note: Could not clear cache file: {e}")
            
    success_count = 0
    for symbol in tickers:
        try:
            print(f"Fetching data for ticker: {symbol} ...")
            change = get_daily_price_change(symbol)
            if change is not None:
                sign = "+" if change >= 0 else ""
                print(f"  -> SUCCESS! Live change for {symbol}: {sign}{change:.2f}%")
                success_count += 1
            else:
                print(f"  -> FAILED: Received None for {symbol}")
        except Exception as e:
            print(f"  -> ERROR fetching {symbol}: {e}")
            
    print("==================================================")
    print(f"Result: {success_count}/{len(tickers)} tickers successfully fetched.")
    print("==================================================")

if __name__ == "__main__":
    test_stocks()
