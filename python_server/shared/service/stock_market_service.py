import requests
import os
import json
from datetime import datetime, timedelta
import logging
from python_server.shared.constants import STOCK_MARKET_BASE_URL, STOCK_CACHE_FILE
from python_server.shared.service.secret import STOCK_MARKET_API_KEY


STOCK_CACHE_DURATION = timedelta(hours=1)  # Cache duration of 1 hour


def get_stock_market_data(function, symbol):
  url = f"{STOCK_MARKET_BASE_URL}?function={function}&symbol={symbol}&apikey={STOCK_MARKET_API_KEY}"
  return requests.get(url)

def load_cached_data(symbol):
  if os.path.exists(STOCK_CACHE_FILE):
    with open(STOCK_CACHE_FILE, 'r') as file:
      data = json.load(file)
      if symbol in data:
        cache_entry = data[symbol]
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        if datetime.now() - cache_time < STOCK_CACHE_DURATION:
          return cache_entry['data']
  return None

def save_to_cache(symbol, api_data):
  cache_data = {}
  if os.path.exists(STOCK_CACHE_FILE):
    with open(STOCK_CACHE_FILE, 'r') as file:
      cache_data = json.load(file)

  cache_data[symbol] = {
    'timestamp': datetime.now().isoformat(),
    'data': api_data
  }

  with open(STOCK_CACHE_FILE, 'w') as file:
    json.dump(cache_data, file)

def get_daily_price_change(symbol):
  """
  This method fetches daily price data from Alpha Vantage API and calculates the daily price change percentage.
  Args:
      symbol (str): The stock symbol (e.g., AAPL)
  Returns:
      float: The daily price change percentage (or None if data unavailable)
  """

  # Check if data is available in the cache
  cached_data = load_cached_data(symbol)
  if cached_data:
    data = cached_data
  else:
    function = "TIME_SERIES_DAILY"
    response = get_stock_market_data(function, symbol)
    if response.status_code == 200:
      data = response.json()

      if "Error Message" in data:
        logging.error(f"Error: {data['Error Message']}")
        return None
      if "Time Series (Daily)" not in data:
        logging.error(f"Error: 'Time Series (Daily)' data not found in the API response.")
        return None

      # Save response to cache
      save_to_cache(symbol, data)
    else:
      logging.error(f"Error: API request failed. Status code: {response.status_code}")
      return None

  # Extract data for the latest trading day
  latest_day = list(data["Time Series (Daily)"].keys())[0]
  latest_close = float(data["Time Series (Daily)"][latest_day]["4. close"])

  # Previous day data (assuming data is available for two days)
  try:
    previous_day = list(data["Time Series (Daily)"].keys())[1]
    previous_close = float(data["Time Series (Daily)"][previous_day]["4. close"])
  except IndexError:
    print("Warning: Insufficient data for calculating daily change.")
    return None

  # Calculate daily price change percentage
  daily_change = ((latest_close - previous_close) / previous_close) * 100
  return daily_change