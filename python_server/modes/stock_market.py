from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
import feedparser
from python_server.shared.constants import GREEN, RED, GOLD
from python_server.shared.service.stock_market_service import get_daily_price_change
def run(stop_event):
    stop_scrolling_text()

    symbol = "AAPL"

    daily_change = get_daily_price_change(symbol)

    if daily_change is not None:
        displayTitle = f"Daily price change for {symbol}: {daily_change:.2f}%"
        print(displayTitle)
        display_on_matrix(displayTitle, GREEN,stop_event)