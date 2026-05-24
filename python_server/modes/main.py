import os
import time
import subprocess
import logging
import feedparser
from python_server.shared.constants import CPP_BINARY_FOLDER, GREEN, GOLD, RED, CYAN, PURPLE
from python_server.shared.service.calendar_service import get_next_calendar_event
from python_server.shared.service.stock_market_service import get_daily_price_change
from python_server.shared.service.atac_service import fetch_atac_arrivals

DASHBOARD_DATA_FILE = "/var/weather/dashboard_data.txt"

# RSS feeds for priority News flashes
ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

STOCKS_TO_TRACK = ["GOOG", "SXR9.DE", "BTC-USD"]
displayed_news = set()

def write_dashboard_data(temp, bottom_left, bl_color, bottom_right, br_color):
    """
    Writes the static dashboard details to the plain text file.
    The C++ dashboard binary reads this file dynamically every 1s to update the display.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DASHBOARD_DATA_FILE), exist_ok=True)
        
        # Truncate strings to fit perfectly on the 64x32 matrix without overlap
        temp_clean = temp[:6]
        bl_clean = bottom_left[:8]
        br_clean = bottom_right[:8]
        
        with open(DASHBOARD_DATA_FILE, "w") as file:
            file.write(f"{temp_clean}\n")
            file.write(f"{bl_clean}\n")
            file.write(f"{bl_color}\n")
            file.write(f"{br_clean}\n")
            file.write(f"{br_color}\n")
    except Exception as e:
        logging.error(f"[Main Features] Failed to write dashboard data: {e}")

def run(stop_event):
    """
    Runs the Feature-Rich Static Dashboard (Mode 8).
    Starts the native C++ 'dashboard' program in the background, and cycles through
    different information slots in Python, writing them to a shared status file.
    """
    logging.info("[Main Features] Starting Feature-Rich Static Dashboard Mode...")
    
    # 1. Gather initial data and write to file
    from python_server.shared.service.weather_service import get_weather_rome
    try:
        temp = str(get_weather_rome()["main"]["temp"]) + "°C"
    except Exception:
        temp = "--°C"
        
    write_dashboard_data(temp, "Caricam.", CYAN, "Attend.", GREEN)

    # 2. Populate initial RSS news to only trigger flashes for *new* news
    rss_feeds = [ANSA_RSS_FEED_URL, BALLKANWEB_RSS_FEED_URL, BBC_RSS_FEED_URL]
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if "title" in entry:
                    displayed_news.add(entry.title)
        except Exception:
            pass

    # 3. Spawn C++ dashboard process in the background
    cpp_dashboard = os.path.join(CPP_BINARY_FOLDER, 'dashboard')
    cmd = [
        "sudo", cpp_dashboard,
        "-f", "../fonts/6x13.bdf",  # Clock font
        "-s", "../fonts/4x6.bdf",   # Compact widget font
        "-i", DASHBOARD_DATA_FILE,
        "--led-no-hardware-pulse",
        "--led-cols=64",
        "--led-gpio-mapping=adafruit-hat",
        "--led-slowdown-gpio=4"
    ]

    process = None
    try:
        logging.info(f"[Main Features] Spawning C++ Dashboard: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logging.error(f"[Main Features] Failed to spawn C++ Dashboard: {e}")
        return

    # Cycle state variables
    last_weather_fetch = 0
    last_widget_rotate = 0
    current_pane = 0  # 0: Calendar + Stocks, 1: ATAC Bus Arrivals, 2: Priority News

    temp_cache = temp
    stock_idx = 0

    while not stop_event.is_set():
        current_time = time.time()

        # A. Fetch Weather every 10 minutes
        if current_time - last_weather_fetch >= 600:
            try:
                temp_cache = str(get_weather_rome()["main"]["temp"]) + "°C"
                last_weather_fetch = current_time
            except Exception as e:
                logging.error(f"[Main Features] Failed to fetch weather: {e}")

        # B. Check for priority news flashes (Interrupts current flow)
        new_headline = None
        for url in rss_feeds:
            if stop_event.is_set():
                break
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if "title" in entry and entry.title not in displayed_news:
                        new_headline = entry.title
                        displayed_news.add(new_headline)
                        break
                if new_headline:
                    break
            except Exception:
                pass

        if new_headline:
            logging.info(f"[Main Features] PRIORITY NEWS FLASH: {new_headline}")
            # Alert flash on the bottom riquadro for 10 seconds
            write_dashboard_data(temp_cache, "FLASH", RED, new_headline, GOLD)
            time.sleep(10)
            continue

        # C. Rotate Widgets Pane every 5 seconds
        if current_time - last_widget_rotate >= 5.0:
            current_pane = (current_pane + 1) % 2  # Toggle between Calendar/Stocks and ATAC arrivals
            last_widget_rotate = current_time

            if current_pane == 0:
                # --- PANE 1: Calendar (Left) & Stocks (Right) ---
                bl_text = "Nessuno"
                bl_color = CYAN
                try:
                    event = get_next_calendar_event()
                    if event:
                        bl_text = f"{event['time']} {event['title']}"
                except Exception:
                    pass

                br_text = ""
                br_color = GREEN
                try:
                    # Pick a stock dynamically from the list
                    symbol = STOCKS_TO_TRACK[stock_idx]
                    change = get_daily_price_change(symbol)
                    display_symbol = symbol.split(".")[0].split("-")[0]
                    if change is not None:
                        sign = "+" if change >= 0 else ""
                        br_text = f"{display_symbol}{sign}{change:.1f}%"
                        br_color = GREEN if change >= 0 else RED
                    else:
                        br_text = f"{display_symbol} --"
                    stock_idx = (stock_idx + 1) % len(STOCKS_TO_TRACK)
                except Exception:
                    br_text = "Stocks"

                write_dashboard_data(temp_cache, bl_text, bl_color, br_text, br_color)

            elif current_pane == 1:
                # --- PANE 2: ATAC Arrivals ---
                bl_text = "ATAC 74029"
                bl_color = GOLD
                br_text = "--"
                br_color = GOLD
                try:
                    stop_name, arrivals = fetch_atac_arrivals("74029")
                    if arrivals:
                        # Display up to 2 lines
                        if len(arrivals) >= 1:
                            bl_text = f"{arrivals[0]['line']}:{arrivals[0]['prediction'].split()[0]}"
                        if len(arrivals) >= 2:
                            br_text = f"{arrivals[1]['line']}:{arrivals[1]['prediction'].split()[0]}"
                    else:
                        # Skip this pane entirely if fetch fails
                        current_pane = 0
                        last_widget_rotate = 0  # Force immediate rerender of Pane 0
                        continue
                except Exception:
                    # Graceful skip
                    current_pane = 0
                    last_widget_rotate = 0
                    continue

                write_dashboard_data(temp_cache, bl_text, bl_color, br_text, br_color)

        time.sleep(0.5)  # Responsive loop checking stop_event

    # 4. Clean up background process
    if process:
        try:
            if process.poll() is None:
                process.terminate()
                process.wait()
            logging.info("[Main Features] Dashboard background process terminated.")
        except Exception as e:
            logging.error(f"[Main Features] Error stopping C++ dashboard process: {e}")

    logging.info("[Main Features] Stopped Feature-Rich Static Dashboard Mode.")