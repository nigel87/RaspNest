"""
Quick diagnostic: find the correct Yahoo Finance tickers for Nigel's ETFs.
Run from the RaspNest root: python3 python_server/test_stocks.py
"""
import yfinance as yf

# Base tickers (from Trade Republic / Xetra)
# We try common exchange suffixes to find which one Yahoo Finance knows
CANDIDATES = {
    "S&P500 (SXR9)": [
        "SXR9.DE", "SXR9.F", "SXR9.XETRA", "CSPX.L", "CSPX.MI",
    ],
    "MSCI Europe IT (ESIT)": [
        "ESIT.MI", "ESIT.DE", "ESIT.F", "ESIT.L", "IUIT.L", "IUIT.MI",
    ],
    "Europe Defence (DFNC)": [
        "DFNC.L", "DFNC.DE", "DFNC.F", "DFNC.MI", "DFNC.AS",
    ],
    "GOOG (control)": [
        "GOOG",
    ],
}

print("=" * 60)
for name, tickers in CANDIDATES.items():
    print(f"\n>>> {name}")
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="5d")
            if not hist.empty and len(hist) >= 2:
                latest   = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[-2]
                change   = ((latest - previous) / previous) * 100
                sign     = "+" if change > 0 else ""
                print(f"  ✅ {t:<15}  close={latest:.4f}  day={sign}{change:.2f}%")
            else:
                print(f"  ❌ {t:<15}  (no data / hist empty)")
        except Exception as e:
            print(f"  💥 {t:<15}  error: {e}")
print("\n" + "=" * 60)
print("Use the ✅ ticker in stock_market.py")
