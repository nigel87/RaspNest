import sys
import os
import cherrypy
import threading
import logging

# --- Logging Setup ---
logging.basicConfig(filename='logs/raspnest.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append('../')  # Adjust the path as needed based on your project structure

from python_server.modes import clock_and_weather, news, weather_detail, football, stock_market, system_info, main, image_display
from python_server.shared.controller.matrix_controller import stop_scrolling_text
from python_server.shared.constants import *
from python_server.modes.clock_and_weather import stop_clock

# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configure CherryPy to listen on a specific host (e.g., 192.168.1.143)
cherrypy.config.update({'server.socket_host': '192.168.1.144'})

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
    9: {"name": "Image Display", "run_function": image_display.run, "args": ("../assets/gif/Fireplace.gif",)}

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
            self.current_thread = threading.Thread(
                target=mode_info["run_function"],
                args=mode_info.get("args", ()) + (self.stop_event,)
            )
            self.current_thread.start()
            return {"message": f"Mode {mode} ({mode_info['name']}) started"}
        except KeyError:
            return {"message": "Invalid mode"}

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
    cherrypy.quickstart(LEDMatrixDisplayService(), '/', {
        '/': {
            'tools.enable_cors.on': True
        }
    })
