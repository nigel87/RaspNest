import sys
import os
import cherrypy
import threading
import logging

# --- Logging Setup ---
logging.basicConfig(filename='logs/raspnest.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append('../')  # Adjust the path as needed based on your project structure

from python_server.modes import clock_and_weather, news, weather_detail, football, stock_market, system_info, main, image_display, youtube_music, atac_bus, retro_gaming, outrun, cyberpunk, sand_physics, aquarium, clock_and_weather_news, main_cozy, night_mode
from python_server.shared.controller.matrix_controller import stop_scrolling_text, run_clock_with_scrolling_text
from python_server.shared.constants import *
from python_server.modes.clock_and_weather import stop_clock
from python_server.shared.service import nest_music_monitor

# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configure CherryPy to listen on a specific host and disable the autoreloader in production
cherrypy.config.update({
    'server.socket_host': '192.168.1.144',
    'engine.autoreload.on': False
})

# Safeguard: fully unsubscribe CherryPy's autoreloader plugin to ensure it never restarts the process
if hasattr(cherrypy.engine, 'autoreload'):
    cherrypy.engine.autoreload.unsubscribe()

MODES = {
    0: {"name": "News (ANSA)", "run_function": news.run, "args": (ANSA_RSS_FEED_URL,)},
    1: {"name": "News (BalkanWeb)", "run_function": news.run, "args": (BALLKANWEB_RSS_FEED_URL,)},
    2: {"name": "News (BBC)", "run_function": news.run, "args": (BBC_RSS_FEED_URL,)},
    3: {"name": "Clock & News (Old Main)", "run_function": clock_and_weather_news.run, "args": ()},
    4: {"name": "Weather Detail", "run_function": weather_detail.run, "args": ()},
    5: {"name": "Football", "run_function": football.run, "args": ()},
    6: {"name": "Stock Market", "run_function": stock_market.run, "args": ()},
    7: {"name": "System Info", "run_function": system_info.run, "args": ()},
    8: {"name": "Main Mode (Feature Rich)", "run_function": main.run, "args": ()},
    9: {"name": "Image Display", "run_function": image_display.run, "args": ("../assets/gif/Fireplace.gif",)},
    10: {"name": "YouTube Music", "run_function": youtube_music.run, "args": ()},
    11: {"name": "ATAC Bus 74029", "run_function": atac_bus.run, "args": ()},
    12: {"name": "Retro Pixel Art", "run_function": retro_gaming.run, "args": ()},
    13: {"name": "Outrun Highway", "run_function": outrun.run, "args": ()},
    14: {"name": "Cozy Cyberpunk", "run_function": cyberpunk.run, "args": ()},
    15: {"name": "Sand Physics", "run_function": sand_physics.run, "args": ()},
    16: {"name": "Cozy Virtual Aquarium", "run_function": aquarium.run, "args": ()},
    17: {"name": "Main Mode (Cozy Minimalist)", "run_function": main_cozy.run, "args": ()},
    18: {"name": "Cozy Night Mode", "run_function": night_mode.run, "args": ()}
}

TOTAL_NUMBER_OF_MODES = len(MODES)


class LEDMatrixDisplayService:
    def __init__(self):
        self.current_mode = 0  # Initialize the current mode
        self.current_thread = None  # Initialize the current running thread
        self.stop_event = threading.Event()  # Event to signal stopping the current mode

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def display_message(self):
        if cherrypy.request.method == 'OPTIONS':
            # Respond to preflight request
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            cherrypy.response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight response for 1 hour
            return ''

        # Handle POST request
        data = cherrypy.request.json
        mode = data.get('mode', None)  # No default mode here to allow cycling
        text = data.get('text', 'Hello, World!')  # Default text

        # If no mode is specified, redirect to the smart contextual action button logic immediately.
        # This prevents stopping the thread (and clearing the scrolling news state) prematurely!
        if mode is None:
            return self.action_button()

        # Signal the current thread to stop and wait for it to finish
        if self.current_thread and self.current_thread.is_alive() and threading.current_thread() != self.current_thread:
            self.stop_event.set()
            self.current_thread.join()
            stop_scrolling_text()
            stop_clock()

        # Reset the stop event for the new mode
        self.stop_event.clear()

        mode = int(mode)

        # Run the corresponding mode using the dictionary
        try:
            mode_info = MODES[mode]
            run_args = list(mode_info.get("args", ())) # Convert to list to modify

            if mode == 9: # Special handling for image display mode
                if text:
                    image_path = os.path.join("../assets", text)
                else:
                    image_path = "../assets/gif/Fireplace.gif" # Default image
                run_args = [image_path]
            elif mode == 10: # Special handling for YouTube Music mode
                artist = data.get('artist', 'Unknown Artist')
                image_path = data.get('image_path', TEMP_ALBUM_ART_PATH)
                run_args = [text, artist, image_path]

            self.current_thread = threading.Thread(
                target=mode_info["run_function"],
                args=tuple(run_args) + (self.stop_event,),
                daemon=True
            )
            self.current_thread.start()
            return {"message": f"Mode {mode} ({mode_info['name']}) started"}
        except KeyError:
            return {"message": "Invalid mode"}

    def trigger_mode_change(self, mode_id, text="Hello, World!", artist="Unknown Artist", image_path=None):
        """
        Thread-safe internal hook allowing background threads (e.g. Nest Monitor)
        to transition matrix display modes programmatically.
        """
        logging.info(f"Local request to start mode {mode_id}")
        
        # Stop current running thread
        if self.current_thread and self.current_thread.is_alive() and threading.current_thread() != self.current_thread:
            self.stop_event.set()
            self.current_thread.join()
            stop_scrolling_text()
            stop_clock()

        self.stop_event.clear()
        
        if int(mode_id) == -1:
            logging.info("Display turned off successfully (stopping all active controllers).")
            self.current_mode = -1
            return

        self.current_mode = int(mode_id)

        try:
            mode_info = MODES[self.current_mode]
            run_args = list(mode_info.get("args", ()))

            if self.current_mode == 10:
                run_args = [text, artist, image_path or TEMP_ALBUM_ART_PATH]
            elif self.current_mode == 9:
                run_args = [image_path or "../assets/gif/Fireplace.gif"]

            self.current_thread = threading.Thread(
                target=mode_info["run_function"],
                args=tuple(run_args) + (self.stop_event,),
                daemon=True
            )
            self.current_thread.start()
            logging.info(f"Successfully started mode {self.current_mode} via local trigger.")
        except KeyError:
            logging.error(f"Invalid mode {self.current_mode} requested via local trigger.")
        except Exception as e:
            logging.error(f"Error starting mode {self.current_mode} via local trigger: {e}")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def drop_sand(self):
        if cherrypy.request.method == 'OPTIONS':
            # Respond to preflight request
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            cherrypy.response.headers['Access-Control-Max-Age'] = '3600'
            return ''

        data = cherrypy.request.json or {}
        x = data.get('x', 32)
        color = data.get('color', None)

        color_tuple = None
        if isinstance(color, list) and len(color) == 3:
            color_tuple = tuple(color)

        # Enqueue the sand pixel
        from python_server.modes.sand_physics import sand_queue
        sand_queue.put({"x": x, "color": color_tuple})
        return {"status": "success", "message": f"Sand pixel queued at column {x}"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def feed_fish(self):
        if cherrypy.request.method == 'OPTIONS':
            # Respond to preflight request
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            cherrypy.response.headers['Access-Control-Max-Age'] = '3600'
            return ''

        import random
        from python_server.modes.aquarium import food_queue
        food_queue.put({"x": random.randint(5, 58), "y": 0, "id": random.random()})
        return {"status": "success", "message": "Fish food dropped!"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def action_button(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            return ''

        # Read the current context from state
        from python_server.shared import state
        is_news = False
        active_news = None
        with state.state_lock:
            is_news = state.is_news_scrolling
            if state.current_news_entry:
                active_news = dict(state.current_news_entry)

        # 1. Context: News is scrolling in Main mode (mode 8)
        if self.current_mode == 8 and is_news and active_news:
            logging.info(f"Context Action: Displaying full details for news: '{active_news['title']}'")
            
            # Stop the Main mode thread
            if self.current_thread and self.current_thread.is_alive():
                self.stop_event.set()
                self.current_thread.join()
                stop_scrolling_text()
                stop_clock()

            self.stop_event.clear()

            # Clean HTML from RSS summary
            import re
            def clean_html(raw_html):
                cleanr = re.compile('<.*?>')
                cleantext = re.sub(cleanr, '', raw_html)
                cleantext = re.sub(r'\s+', ' ', cleantext).strip()
                return cleantext

            summary_clean = clean_html(active_news.get("summary", ""))
            if summary_clean:
                detail_text = f"{active_news['title']} -- {summary_clean}"
            else:
                detail_text = active_news['title']

            if len(detail_text) > 300:
                detail_text = detail_text[:300] + "..."

            # Function to scroll details twice
            def scroll_details_twice(text, stop_event):
                # Run clock with scrolling text twice
                for _ in range(2):
                    if stop_event.is_set():
                        break
                    run_clock_with_scrolling_text(text, GREEN, GOLD, stop_event)

                # Automatically resume Main mode
                if not stop_event.is_set():
                    logging.info("Details scrolling finished. Auto-resuming Main mode.")
                    self.trigger_mode_change(8)

            # Start detail scroller thread
            self.current_thread = threading.Thread(
                target=scroll_details_twice,
                args=(detail_text, self.stop_event),
                daemon=True
            )
            self.current_thread.start()
            return {"message": "News details started scrolling", "context": "news_details"}

        # 2. Context: Favorites cycling (Feature Mode [8] -> Aquarium [16] -> Sand Physics [15])
        favorites = [8, 16, 15]
        if self.current_mode not in favorites:
            next_mode = 8
        else:
            idx = favorites.index(self.current_mode)
            next_mode = favorites[(idx + 1) % len(favorites)]

        logging.info(f"Cycling from mode {self.current_mode} to next favorite: {next_mode}")
        self.trigger_mode_change(next_mode)
        mode_name = MODES[next_mode]["name"]
        return {"message": f"Started {mode_name}", "context": "favorite_cycle", "mode": next_mode}

    def night_mode_monitor(self):
        logging.info("Night mode background monitor started.")
        last_checked_hour = -1
        while True:
            try:
                now = time.localtime()
                current_hour = now.tm_hour
                
                if current_hour != last_checked_hour:
                    # Transition to 1:00 AM (Activate dim Night Mode)
                    if current_hour == 1:
                        logging.info("01:00 AM reached. Activating automatic Cozy Night Mode (mode 18).")
                        self.trigger_mode_change(18)
                        last_checked_hour = current_hour
                    # Transition to 7:00 AM (Deactivate Night Mode, start Feature Mode)
                    elif current_hour == 7:
                        logging.info("07:00 AM reached. Deactivating Night Mode (starting Feature Mode 8).")
                        self.trigger_mode_change(8)
                        last_checked_hour = current_hour
                    else:
                        last_checked_hour = current_hour

                time.sleep(30)
            except Exception as e:
                logging.error(f"Error in night_mode_monitor: {e}")
                time.sleep(30)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def list_assets(self):
        assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets'))
        logging.info(f"Listing assets from: {assets_path}")
        asset_structure = {}
        try:
            for root, dirs, files in os.walk(assets_path):
                relative_path = os.path.relpath(root, assets_path)
                if relative_path == '.':
                    current_folder = "/"
                else:
                    current_folder = relative_path.replace(os.sep, '/')
                
                asset_structure[current_folder] = files
            logging.info("Assets listed successfully.")
            return {"status": "success", "assets": asset_structure}
        except Exception as e:
            logging.error(f"Error listing assets: {e}")
            cherrypy.response.status = 500
            return {"status": "error", "message": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_widget_config(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            return ''
            
        try:
            import json
            from python_server.shared.constants import WIDGET_CONFIG_FILE
            if os.path.exists(WIDGET_CONFIG_FILE):
                with open(WIDGET_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error reading widget config: {e}")
            
        return {
            "top_widget": "atac_bus",
            "bottom_left_widget": "calendar",
            "bottom_right_widget": "stocks"
        }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def configure_widgets(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            return ''
            
        try:
            import json
            from python_server.shared.constants import WIDGET_CONFIG_FILE
            
            # Read and parse the raw request body manually
            cl = cherrypy.request.headers.get('Content-Length', 0)
            raw_body = cherrypy.request.body.read(int(cl)).decode('utf-8')
            data = json.loads(raw_body)
            
            os.makedirs(os.path.dirname(WIDGET_CONFIG_FILE), exist_ok=True)
            with open(WIDGET_CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
                
            logging.info(f"Saved new widget configuration: {data}")
            return {"status": "success", "message": "Widget layout updated successfully"}
        except Exception as e:
            logging.error(f"Error saving widget config: {e}")
            cherrypy.response.status = 500
            return {"status": "error", "message": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def configure_fun_mode(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            return ''
            
        try:
            import json
            FUN_MODE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "fun_mode.json"))
            
            # Read and parse the raw request body manually
            cl = cherrypy.request.headers.get('Content-Length', 0)
            raw_body = cherrypy.request.body.read(int(cl)).decode('utf-8')
            data = json.loads(raw_body)
            mode = int(data.get("mode", 16))
            
            os.makedirs(os.path.dirname(FUN_MODE_FILE), exist_ok=True)
            with open(FUN_MODE_FILE, 'w') as f:
                json.dump({"mode": mode}, f, indent=4)
                
            logging.info(f"Saved fun mode configuration: {mode}")
            return {"status": "success", "message": f"Fun mode set to {mode}"}
        except Exception as e:
            logging.error(f"Error saving fun mode config: {e}")
            cherrypy.response.status = 500
            return {"status": "error", "message": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def current_state(self):
        if cherrypy.request.method == 'OPTIONS':
            cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
            return ''
            
        # Read widget config
        widget_config = {
            "top_widget": "atac_bus",
            "bottom_left_widget": "calendar",
            "bottom_right_widget": "stocks"
        }
        try:
            import json
            from python_server.shared.constants import WIDGET_CONFIG_FILE
            if os.path.exists(WIDGET_CONFIG_FILE):
                with open(WIDGET_CONFIG_FILE, 'r') as f:
                    widget_config = json.load(f)
        except Exception:
            pass

        # Read fun mode
        fun_mode = 16
        try:
            import json
            FUN_MODE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "fun_mode.json"))
            if os.path.exists(FUN_MODE_FILE):
                with open(FUN_MODE_FILE, 'r') as f:
                    fun_mode = json.load(f).get("mode", 16)
        except Exception:
            pass

        # Read music state
        from python_server.shared import state
        music_state = {
            "is_playing": False,
            "title": "",
            "artist": ""
        }
        with state.state_lock:
            music_state["is_playing"] = state.is_music_playing
            music_state["title"] = state.music_title
            music_state["artist"] = state.music_artist

        return {
            "current_mode": self.current_mode,
            "music": music_state,
            "widget_config": widget_config,
            "fun_mode": fun_mode
        }

# Enable CORS globally using a custom tool
def enable_cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

# Register the CORS tool
cherrypy.tools.enable_cors = cherrypy.Tool('before_handler', enable_cors)


if __name__ == '__main__':
    service = LEDMatrixDisplayService()
    
    # Start Google Nest Mini local casting monitor daemon
    try:
        nest_music_monitor.start_monitoring(service)
    except Exception as e:
        logging.error(f"Failed to start Nest Music Monitor discovery: {e}")

    # Start the Night Mode background daemon
    try:
        night_thread = threading.Thread(target=service.night_mode_monitor, daemon=True)
        night_thread.start()
        logging.info("Night Mode background daemon started successfully.")
    except Exception as e:
        logging.error(f"Failed to start Night Mode monitor daemon: {e}")
        
    # Auto-start appropriate mode based on time of day (Night Mode 18 at night, Feature Mode 8 during the day)
    try:
        import time
        now_hour = time.localtime().tm_hour
        if 1 <= now_hour < 7:
            service.trigger_mode_change(18)
            logging.info("Auto-started Cozy Night Mode (mode 18) at server launch (Night hours).")
        else:
            service.trigger_mode_change(8)
            logging.info("Auto-started Feature Mode (mode 8) at server launch (Day hours).")
    except Exception as e:
        logging.error(f"Failed to auto-start default mode at launch: {e}")
        
    cherrypy.quickstart(service, '/', {
        '/': {
            'tools.enable_cors.on': True
        }
    })
