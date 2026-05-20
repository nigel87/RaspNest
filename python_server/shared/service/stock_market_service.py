import yfinance as yf
import os
import json
from datetime import datetime, timedelta
import logging

STOCK_CACHE_FILE = "/var/weather/stock_data_cache.json"
STOCK_CACHE_DURATION = timedelta(hours=1)  # Cache duration of 1 hour


def load_cached_data(symbol):
    if os.path.exists(STOCK_CACHE_FILE):
        with open(STOCK_CACHE_FILE, 'r') as file:
            try:
                data = json.load(file)
                if symbol in data:
                    cache_entry = data[symbol]
                    cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                    if datetime.now() - cache_time < STOCK_CACHE_DURATION:
                        value = cache_entry['data']
                        # Guard against old Alpha Vantage dict-format cache entries
                        if isinstance(value, (int, float)):
                            return value
            except (json.JSONDecodeError, KeyError):
                pass
    return None


def save_to_cache(symbol, change_pct):
    cache_data = {}
    if os.path.exists(STOCK_CACHE_FILE):
        try:
            with open(STOCK_CACHE_FILE, 'r') as file:
                cache_data = json.load(file)
        except (json.JSONDecodeError, IOError):
            pass

    cache_data[symbol] = {
        'timestamp': datetime.now().isoformat(),
        'data': change_pct
    }

    with open(STOCK_CACHE_FILE, 'w') as file:
        json.dump(cache_data, file)


def get_daily_price_change(symbol):
    """
    Fetches the daily price change percentage using Yahoo Finance.
    Works for US stocks (GOOG) and European ETFs (SXR9.DE, ESIT.MI, DFNC.L).

    Args:
        symbol (str): Yahoo Finance ticker (e.g. 'GOOG', 'SXR9.DE')
    Returns:
        float: Daily price change percentage, or None if unavailable.
    """
    # Return from cache if fresh
    cached = load_cached_data(symbol)
    if cached is not None:
        logging.info(f"[Stock Cache] {symbol}: {cached:.2f}%")
        return cached

    try:
        ticker = yf.Ticker(symbol)
        # Fetch last 5 days to ensure we always have at least 2 trading days
        hist = ticker.history(period="5d")

        if hist.empty or len(hist) < 2:
            logging.error(f"[Stock] Not enough data for {symbol}")
            return None

        latest_close   = hist["Close"].iloc[-1]
        previous_close = hist["Close"].iloc[-2]

        if previous_close == 0:
            return None

        daily_change = ((latest_close - previous_close) / previous_close) * 100
        save_to_cache(symbol, daily_change)
        return daily_change

    except Exception as e:
        logging.error(f"[Stock] Error fetching {symbol}: {e}")
        return None