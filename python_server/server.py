import sys
import os
import cherrypy
import threading
import logging

# --- Logging Setup ---
logging.basicConfig(filename='logs/raspnest.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append('../')  # Adjust the path as needed based on your project structure

from python_server.modes import clock_and_weather, news, weather_detail, football, stock_market, system_info, main, image_display, youtube_music, atac_bus, retro_gaming, outrun, cyberpunk, sand_physics
from python_server.shared.controller.matrix_controller import stop_scrolling_text
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
    3: {"name": "Clock and Weather", "run_function": clock_and_weather.run, "args": ()},
    4: {"name": "Weather Detail", "run_function": weather_detail.run, "args": ()},
    5: {"name": "Football", "run_function": football.run, "args": ()},
    6: {"name": "Stock Market", "run_function": stock_market.run, "args": ()},
    7: {"name": "System Info", "run_function": system_info.run, "args": ()},
    8: {"name": "Main", "run_function": main.run, "args": ()},
    9: {"name": "Image Display", "run_function": image_display.run, "args": ("../assets/gif/Fireplace.gif",)},
    10: {"name": "YouTube Music", "run_function": youtube_music.run, "args": ()},
    11: {"name": "ATAC Bus 74029", "run_function": atac_bus.run, "args": ()},
    12: {"name": "Retro Pixel Art", "run_function": retro_gaming.run, "args": ()},
    13: {"name": "Outrun Highway", "run_function": outrun.run, "args": ()},
    14: {"name": "Cozy Cyberpunk", "run_function": cyberpunk.run, "args": ()},
    15: {"name": "Sand Physics", "run_function": sand_physics.run, "args": ()}
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

        # Signal the current thread to stop and wait for it to finish
        if self.current_thread and self.current_thread.is_alive():
            self.stop_event.set()
            self.current_thread.join()
            stop_scrolling_text()
            stop_clock()

        # Reset the stop event for the new mode
        self.stop_event.clear()

        # If no mode is specified, cycle to the next mode
        if mode is None:
            self.current_mode = (self.current_mode + 1) % TOTAL_NUMBER_OF_MODES
            mode = self.current_mode
        else:
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
                run_args.append(image_path)
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
        if self.current_thread and self.current_thread.is_alive():
            self.stop_event.set()
            self.current_thread.join()
            stop_scrolling_text()
            stop_clock()

        self.stop_event.clear()
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

# Enable CORS globally using a custom tool
def enable_cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
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
        
    cherrypy.quickstart(service, '/', {
        '/': {
            'tools.enable_cors.on': True
        }
    })
