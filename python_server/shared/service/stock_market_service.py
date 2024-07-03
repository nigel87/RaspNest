import requests

from python_server.shared.constants import STOCK_MARKET_BASE_URL
from python_server.shared.service.secret import STOCK_MARKET_API_KEY

def get_stock_market_data(function,symbol):
  url = f"{STOCK_MARKET_BASE_URL}?function={function}&symbol={symbol}&apikey={STOCK_MARKET_API_KEY}"
  return requests.get(url)

  

def get_daily_price_change(symbol):
  """
  This method fetches daily price data from Alpha Vantage API and calculates the daily price change percentage.
  Args:
      symbol (str): The stock symbol (e.g., AAPL)
  Returns:
      float: The daily price change percentage (or None if data unavailable)
  """

  

  function = "TIME_SERIES_DAILY"
  response = get_stock_market_data(function,symbol)

  if response.status_code == 200:
    data = response.json()

    if "Error Message" in data:
      print(f"Error: {data['Error Message']}")
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
  else:
    print(f"Error: API request failed. Status code: {response.status_code}")
    return None



