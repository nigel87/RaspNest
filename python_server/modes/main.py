import os
import time
import subprocess
import logging
import feedparser
import json
import requests
from datetime import datetime
from python_server.shared.constants import CPP_BINARY_FOLDER, GREEN, GOLD, RED, CYAN, PURPLE
from python_server.shared.service.calendar_service import get_next_calendar_event
from python_server.shared.service.stock_market_service import get_daily_price_change
from python_server.shared.service.atac_service import fetch_atac_arrivals

# ========================================================================
#                     DYNAMIC NEW WIDGETS HELPERS
# ========================================================================

def parse_color_config(config, slot_prefix, default_rgb):
    color_val = config.get(f"{slot_prefix}_color", None)
    if not color_val or color_val.lower() == "default":
        return default_rgb
    
    if color_val.startswith('#'):
        try:
            h = color_val.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            return f"{rgb[0]},{rgb[1]},{rgb[2]}"
        except Exception:
            pass
            
    return color_val

def get_cpu_temp():
    try:
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read().strip()) / 1000.0
    except Exception:
        pass
    return 42.0

def get_cpu_usage():
    try:
        return min(100, round(os.getloadavg()[0] * 100 / os.cpu_count()))
    except Exception:
        return 12

def get_ram_usage():
    try:
        if os.path.exists("/proc/meminfo"):
            meminfo = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        meminfo[parts[0].replace(':', '')] = int(parts[1])
            total = meminfo.get('MemTotal', 1)
            free = meminfo.get('MemFree', 0) + meminfo.get('Buffers', 0) + meminfo.get('Cached', 0)
            used = total - free
            return min(100, round((used / total) * 100))
    except Exception:
        pass
    return 32

def get_ping_latency():
    try:
        cmd = ["ping", "-c", "1", "-W", "1", "8.8.8.8"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if "time=" in line:
                    parts = line.split("time=")
                    if len(parts) >= 2:
                        latency = parts[1].split()[0]
                        return f"P{round(float(latency))}"
    except Exception:
        pass
    return "P--"

def get_calendar_countdown():
    try:
        event = get_next_calendar_event()
        if event and 'time' in event:
            event_time_str = event['time']
            now = datetime.now()
            event_dt = datetime.strptime(event_time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            diff_seconds = (event_dt - now).total_seconds()
            if diff_seconds < 0:
                return "NOW"
            diff_minutes = diff_seconds / 60
            if diff_minutes < 60:
                return f"in {round(diff_minutes)}m"
            else:
                return f"in {round(diff_minutes / 60)}h"
    except Exception:
        pass
    return "Libero"

def get_today_date():
    months_it = {
        1: "Gen", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mag", 6: "Giu",
        7: "Lug", 8: "Ago", 9: "Set", 10: "Ott", 11: "Nov", 12: "Dic"
    }
    now = datetime.now()
    month_str = months_it.get(now.month, now.strftime("%b"))
    return f"{now.day}{month_str}"

def get_air_quality():
    try:
        from python_server.shared.service.secret import WEATHER_API_KEY
        url = "http://api.openweathermap.org/data/2.5/air_pollution"
        params = {
            "lat": 41.9028,
            "lon": 12.4964,
            "appid": WEATHER_API_KEY
        }
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            aqi = data['list'][0]['main']['aqi']
            aqi_labels = {1: "Bono", 2: "Discr", 3: "Mod", 4: "Pess", 5: "Toss"}
            label = aqi_labels.get(aqi, f"AQI:{aqi}")
            return f"AQI:{aqi} {label}"[:8]
    except Exception:
        pass
    return "AQI:ND"

def get_football_live_score():
    try:
        from python_server.shared.service.football_service import get_live_scores
        data = get_live_scores()
        if data and 'matches' in data and len(data['matches']) > 0:
            match = data['matches'][0]
            home_team = match['homeTeam']['tla'] or match['homeTeam']['name'][:3].upper()
            away_team = match['awayTeam']['tla'] or match['awayTeam']['name'][:3].upper()
            home_score = match['score']['fullTime']['homeTeam']
            away_score = match['score']['fullTime']['awayTeam']
            if home_score is None: home_score = 0
            if away_score is None: away_score = 0
            return f"{home_team} {home_score}-{away_score} {away_team}"[:8]
    except Exception:
        pass
    return "No Live"


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
    displayed_news.clear()
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
    last_ping_fetch = 0
    last_tomorrow_weather_fetch = 0
    last_config_load = 0
    last_widget_rotate = 0
    last_rss_fetch = 0
    
    weather_cache = {}
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
        if current_time - last_weather_fetch >= 600 or last_weather_fetch == 0:
            try:
                from python_server.shared.service.weather_service import get_weather_rome
                weather_cache = get_weather_rome()
                temp_cache = f"{round(weather_cache['main']['temp'])}C"
                last_weather_fetch = current_time
            except Exception as e:
                logging.error(f"[Main Features] Failed to fetch weather: {e}")

        # A.5. Fetch Top Widget Data dynamically based on configuration
        top_widget_type = widget_config.get("top_widget", "atac_bus")
        
        if top_widget_type == "cpu_temp":
            t_val = get_cpu_temp()
            cached_bus_pred = f"{round(t_val)}C"
            if t_val < 50:
                cached_bus_color = "0,255,0"    # Green
            elif t_val < 70:
                cached_bus_color = "255,140,0"  # Orange
            else:
                cached_bus_color = "255,0,0"    # Red
        elif top_widget_type == "cpu_usage":
            cached_bus_pred = f"C{get_cpu_usage()}%"
            cached_bus_color = "0,255,255" # Cyan
        elif top_widget_type == "ram_usage":
            cached_bus_pred = f"R{get_ram_usage()}%"
            cached_bus_color = "255,0,255" # Purple
        elif top_widget_type == "ping":
            if current_time - last_ping_fetch >= 10 or last_ping_fetch == 0:
                cached_bus_pred = get_ping_latency()
                cached_bus_color = "0,255,0" # Green
                last_ping_fetch = current_time
        elif top_widget_type == "wind_speed":
            try:
                w_ms = weather_cache.get('wind', {}).get('speed', 0.0)
                w_kh = round(w_ms * 3.6)
                cached_bus_pred = f"W{w_kh}k"
                cached_bus_color = "0,255,255"
            except Exception:
                cached_bus_pred = "W--k"
                cached_bus_color = "150,150,150"
        elif top_widget_type == "humidity":
            try:
                hum = weather_cache.get('main', {}).get('humidity', 0)
                cached_bus_pred = f"H{hum}%"
                cached_bus_color = "0,255,0"
            except Exception:
                cached_bus_pred = "H--%"
                cached_bus_color = "150,150,150"
        elif top_widget_type == "atac_bus":
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

        # Override top color if customized
        cached_bus_color = parse_color_config(widget_config, "top", cached_bus_color)

        # B. Check for priority news flashes (Interrupts current flow)
        new_headline = None
        new_summary = ""
        if widget_config.get("enable_news_flash", True):
            if current_time - last_rss_fetch >= 300 or last_rss_fetch == 0:
                last_rss_fetch = current_time
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
            # Force an immediate widgets restoration on the next iteration
            last_widget_rotate = 0
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
            elif bl_widget_type == "calendar_countdown":
                bl_text = get_calendar_countdown()
                bl_color = CYAN
            elif bl_widget_type == "today_date":
                bl_text = get_today_date()
                bl_color = CYAN
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
            elif br_widget_type == "football_live":
                br_text = get_football_live_score()
                br_color = GREEN if "No Live" not in br_text else "150,150,150"
            elif br_widget_type == "air_quality":
                br_text = get_air_quality()
                br_color = "0,255,255" # Cyan
            elif br_widget_type == "custom_status":
                br_text = widget_config.get("custom_status", "HOME")[:8]
                br_color = GOLD
            # Override bottom left and bottom right colors if customized
            bl_color = parse_color_config(widget_config, "bottom_left", bl_color)
            br_color = parse_color_config(widget_config, "bottom_right", br_color)

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