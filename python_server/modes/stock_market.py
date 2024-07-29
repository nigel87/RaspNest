from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
from python_server.shared.constants import GREEN, RED, GOLD
from python_server.shared.service.stock_market_service import get_daily_price_change
def run(stop_event):
    stop_scrolling_text()
    symbols = ["SPY","AAPL", "GOOG", "MSFT", "AMZN", "NVDA"]




    for symbol in symbols:
        daily_change = get_daily_price_change(symbol)
        if daily_change is not None:
            displayTitle = f"{symbol}: {daily_change:.2f}%"
            print(displayTitle)
            display_on_matrix
            colour = GREEN if daily_change>0 else RED 
            display_on_matrix(displayTitle, colour,stop_event)