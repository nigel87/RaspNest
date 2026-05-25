import os
import time
import subprocess
import logging
import feedparser
import json
from python_server.shared.constants import CPP_BINARY_FOLDER, GREEN, GOLD, RED, CYAN, PURPLE
from python_server.shared.service.calendar_service import get_next_calendar_event
from python_server.shared.service.stock_market_service import get_daily_price_change
from python_server.shared.service.atac_service import fetch_atac_arrivals

DASHBOARD_DATA_FILE = "/var/weather/dashboard_data.txt"

# RSS feeds for priority News flashes
ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

STOCKS_TO_TRACK = ["GOOG", "BTC-USD", "^GSPC", "EXV3.DE"]
displayed_news = set()

def write_dashboard_data(temp, bottom_left, bl_color, bottom_right, br_color, bus_pred="ND", bus_color="150,150,150", is_music_playing="0", music_scroll_text=""):
    """
    Writes the static dashboard details to the plain text file.
    The C++ dashboard binary reads this file dynamically every 1s to update the display.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DASHBOARD_DATA_FILE), exist_ok=True)
        
        # Clean and limit string size to matrix bounds
        temp_clean = temp[:6]
        bl_clean = bottom_left
        br_clean = bottom_right
        bus_clean = bus_pred[:5]
        
        with open(DASHBOARD_DATA_FILE, "w") as file:
            file.write(f"{temp_clean}\n")
            file.write(f"{bl_clean}\n")
            file.write(f"{bl_color}\n")
            file.write(f"{br_clean}\n")
            file.write(f"{br_color}\n")
            file.write(f"{bus_clean}\n")
            file.write(f"{bus_color}\n")
            file.write(f"{is_music_playing}\n")
            file.write(f"{music_scroll_text}\n")
    except Exception as e:
        logging.error(f"[Main Features] Failed to write dashboard data: {e}")

def run(stop_event):
    """
    Runs the Feature-Rich Static Dashboard (Mode 8).
    Starts the native C++ 'dashboard' program in the background, and cycles through
    different information slots in Python, writing them to a shared status file.
    """
    logging.info("[Main Features] Starting Feature-Rich Static Dashboard Mode...")
    
    # Initialize top widget bus 409 cache
    cached_bus_pred = "ND"
    cached_bus_color = "150,150,150"
    
    # 1. Gather initial data and write to file
    from python_server.shared.service.weather_service import get_weather_rome
    try:
        temp = f"{round(get_weather_rome()['main']['temp'])}C"
    except Exception:
        temp = "--C"
        
    write_dashboard_data(temp, "Avvio...", CYAN, "...", GREEN, cached_bus_pred, cached_bus_color)

    # 2. Populate initial RSS news to only trigger flashes for *new* news
    rss_feeds = [ANSA_RSS_FEED_URL, BALLKANWEB_RSS_FEED_URL, BBC_RSS_FEED_URL]
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if "title" in entry:
                    clean_title = entry.title.replace('\n', ' ').replace('\r', ' ').strip()
                    displayed_news.add(clean_title)
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
    last_atac_fetch = 0
    last_tomorrow_weather_fetch = 0
    last_config_load = 0
    last_widget_rotate = 0
    
    widget_config = {
        "top_widget": "atac_bus",
        "bottom_left_widget": "calendar",
        "bottom_right_widget": "stocks"
    }

    temp_cache = temp
    stock_idx = 0

    # Loop-level state variables for widgets
    bl_text = "Avvio..."
    bl_color = CYAN
    br_text = "..."
    br_color = GREEN
    is_playing_str = "0"
    music_text = ""

    last_is_music_playing = None
    last_music_title = None
    last_music_artist = None

    while not stop_event.is_set():
        current_time = time.time()

        # Check reactively if music state has changed
        from python_server.shared import state
        with state.state_lock:
            current_music_playing = state.is_music_playing
            current_music_title = state.music_title
            current_music_artist = state.music_artist

        music_changed = (current_music_playing != last_is_music_playing or
                         current_music_title != last_music_title or
                         current_music_artist != last_music_artist)

        if music_changed:
            last_is_music_playing = current_music_playing
            last_music_title = current_music_title
            last_music_artist = current_music_artist
            
            is_playing_str = "1" if current_music_playing else "0"
            music_text = f"{current_music_artist} - {current_music_title}" if current_music_playing else ""
            
            logging.info(f"[Main Features] Music state changed reactively. Playing: {is_playing_str}, Info: {music_text}")
            write_dashboard_data(
                temp_cache, bl_text, bl_color, br_text, br_color, 
                cached_bus_pred, cached_bus_color, 
                is_music_playing=is_playing_str, music_scroll_text=music_text
            )

        # E. Load Widget Configuration every 5 seconds
        if current_time - last_config_load >= 5.0 or last_config_load == 0:
            last_config_load = current_time
            try:
                from python_server.shared.constants import WIDGET_CONFIG_FILE
                import json
                if os.path.exists(WIDGET_CONFIG_FILE):
                    with open(WIDGET_CONFIG_FILE, 'r') as f:
                        widget_config = json.load(f)
                else:
                    widget_config = {
                        "top_widget": "atac_bus",
                        "bottom_left_widget": "calendar",
                        "bottom_right_widget": "stocks"
                    }
            except Exception as e:
                logging.error(f"[Main Features] Failed to load widget config: {e}")

        # A. Fetch Weather every 10 minutes
        if current_time - last_weather_fetch >= 600:
            try:
                temp_cache = f"{round(get_weather_rome()['main']['temp'])}C"
                last_weather_fetch = current_time
            except Exception as e:
                logging.error(f"[Main Features] Failed to fetch weather: {e}")

        # A.5. Fetch Top Widget Data dynamically based on configuration
        top_widget_type = widget_config.get("top_widget", "atac_bus")
        
        if top_widget_type == "atac_bus":
            if current_time - last_atac_fetch >= 30:
                try:
                    stop_name, arrivals = fetch_atac_arrivals("74029")
                    found_409 = False
                    if arrivals:
                        for arr in arrivals:
                            if arr['line'] == "409":
                                pred_text = arr['prediction']
                                if "Nessun" in pred_text or "nessun" in pred_text:
                                    cached_bus_pred = "ND"
                                    cached_bus_color = "150,150,150"
                                else:
                                    pred = pred_text.split()[0]
                                    if pred == "a": # "a tempo" -> 0'
                                        cached_bus_pred = "0'"
                                        cached_bus_color = "255,0,0" # Red
                                    elif pred.isdigit():
                                        mins = int(pred)
                                        cached_bus_pred = f"{mins}'"
                                        if mins <= 5:
                                            cached_bus_color = "255,0,0" # Red
                                        elif mins <= 12:
                                            cached_bus_color = "255,140,0" # Orange
                                        else:
                                            cached_bus_color = "0,255,0" # Green
                                    else:
                                        cached_bus_pred = f"{pred}'"
                                        cached_bus_color = "255,140,0" # Orange
                                found_409 = True
                                break
                    if not found_409:
                        cached_bus_pred = "ND"
                        cached_bus_color = "150,150,150"
                    last_atac_fetch = current_time
                except Exception as e:
                    logging.error(f"[Main Features] Failed to fetch ATAC for top widget: {e}")
        elif top_widget_type == "tomorrow_weather":
            if current_time - last_tomorrow_weather_fetch >= 900 or last_tomorrow_weather_fetch == 0:
                try:
                    from python_server.shared.service.weather_service import get_tomorrow_weather_rome
                    tomorrow_pred = get_tomorrow_weather_rome()
                    cached_bus_pred = tomorrow_pred
                    cached_bus_color = "255,215,0" # Gold
                    last_tomorrow_weather_fetch = current_time
                except Exception as e:
                    logging.error(f"[Main Features] Failed to fetch tomorrow weather: {e}")
        else: # "none"
            cached_bus_pred = "ND"
            cached_bus_color = "150,150,150"

        # B. Check for priority news flashes (Interrupts current flow)
        new_headline = None
        new_summary = ""
        for url in rss_feeds:
            if stop_event.is_set():
                break
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    clean_title = entry.title.replace('\n', ' ').replace('\r', ' ').strip()
                    if "title" in entry and clean_title not in displayed_news:
                        new_headline = clean_title
                        new_summary = entry.get("summary", entry.get("description", ""))
                        displayed_news.add(clean_title)
                        break
                if new_headline:
                    break
            except Exception:
                pass

        if new_headline:
            logging.info(f"[Main Features] PRIORITY NEWS FLASH: {new_headline}")
            
            # Set news scrolling context in state
            from python_server.shared import state
            with state.state_lock:
                state.is_news_scrolling = True
                state.current_news_entry = {
                    "title": new_headline,
                    "summary": new_summary
                }
                
            try:
                write_dashboard_data(temp_cache, "FLASH", RED, new_headline, GOLD, cached_bus_pred, cached_bus_color, is_music_playing="0", music_scroll_text="")
                
                # Dynamically calculate the perfect sleep duration so the entire headline scrolls across the screen
                # BDF 4x6 character width is 4px plus 1px letter spacing (5px total)
                headline_width = len(new_headline) * 5
                clipping_boundary = 2 + len("FLASH") * 5 + 2 # ~29px
                max_br_width = 64 - clipping_boundary - 2 # ~33px
                
                if headline_width <= max_br_width:
                    display_time = 8.0 # Fits statically, show for 8 seconds
                else:
                    display_time = (64 + headline_width) * 0.060 # Exact scroll duration in seconds
                    
                logging.info(f"[Main Features] Sleeping for dynamic duration: {display_time:.1f}s")
                
                # Check for stop_event every 100ms to react immediately to action button presses
                start_time = time.time()
                while time.time() - start_time < display_time:
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
            finally:
                with state.state_lock:
                    state.is_news_scrolling = False
                    state.current_news_entry = None
            
            # Force music state redraw on next iteration by resetting cached music state
            last_is_music_playing = None
            continue

        # C. Rotate Widgets on the bottom row every 5 seconds
        if current_time - last_widget_rotate >= 5.0 or last_widget_rotate == 0:
            last_widget_rotate = current_time

            # --- Bottom Left Widget ---
            bl_widget_type = widget_config.get("bottom_left_widget", "calendar")
            bl_text = "Libero"
            bl_color = CYAN
            
            if bl_widget_type == "calendar":
                try:
                    event = get_next_calendar_event()
                    if event:
                        bl_text = event['time']
                except Exception:
                    pass
            elif bl_widget_type == "news":
                bl_text = "News"
                bl_color = GOLD
            else: # "none"
                bl_text = ""

            # --- Bottom Right Widget ---
            br_widget_type = widget_config.get("bottom_right_widget", "stocks")
            br_text = ""
            br_color = GREEN
            
            if br_widget_type == "stocks":
                try:
                    # Pick a stock dynamically from the list
                    symbol = STOCKS_TO_TRACK[stock_idx]
                    change = get_daily_price_change(symbol)
                    
                    # Custom translation map for tickers
                    display_map = {
                        "GOOG": "GOOG",
                        "BTC-USD": "BTC",
                        "^GSPC": "SP500",
                        "EXV3.DE": "EXV3"
                    }
                    display_symbol = display_map.get(symbol, symbol.split(".")[0].split("-")[0])
                    if change is not None:
                        sign = "+" if change >= 0 else ""
                        br_text = f"{display_symbol}{sign}{change:.1f}%"
                        br_color = GREEN if change >= 0 else RED
                    else:
                        br_text = f"{display_symbol} --"
                    stock_idx = (stock_idx + 1) % len(STOCKS_TO_TRACK)
                except Exception:
                    br_text = "Stocks"
            elif br_widget_type == "news":
                try:
                    # Grab a dynamic headline from ANSA feed
                    import feedparser
                    feed = feedparser.parse(ANSA_RSS_FEED_URL)
                    if feed.entries:
                        latest_title = feed.entries[0].title
                        latest_clean = latest_title.replace('\n', ' ').replace('\r', ' ').strip()
                        # Shorten to fit 7 chars nicely
                        br_text = latest_clean[:7]
                        br_color = GOLD
                    else:
                        br_text = "News"
                        br_color = GOLD
                except Exception:
                    br_text = "News"
                    br_color = GOLD
            else: # "none"
                br_text = ""

            write_dashboard_data(temp_cache, bl_text, bl_color, br_text, br_color, cached_bus_pred, cached_bus_color, is_music_playing=is_playing_str, music_scroll_text=music_text)

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