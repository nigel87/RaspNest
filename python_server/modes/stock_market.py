from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
from python_server.shared.constants import GREEN, RED, GOLD
from python_server.shared.service.stock_market_service import get_daily_price_change
import logging

def run(stop_event):
    stop_scrolling_text()

    # Nigel's investments — Yahoo Finance tickers (verified)
    investments = [
        ("CSPX.L",  "S&P500"),   # iShares Core S&P 500 USD (Acc) — London
        ("ESIT.DE", "EU IT"),    # iShares MSCI Europe Information Technology — Xetra
        ("GOOG",    "GOOG"),     # Alphabet (A)
        ("DFNC.DE", "EU DEF"),   # iShares Europe Defence EUR (Acc) — Xetra
    ]

    for ticker, label in investments:
        if stop_event.is_set():
            break
        daily_change = get_daily_price_change(ticker)
        if daily_change is not None:
            sign = "+" if daily_change > 0 else ""
            displayTitle = f"{label}: {sign}{daily_change:.2f}%"
            logging.info(displayTitle)
            colour = GREEN if daily_change > 0 else RED
            display_on_matrix(displayTitle, colour, stop_event)
        else:
            logging.warning(f"No data for {ticker} ({label})")