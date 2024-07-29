import sys
import os
import cherrypy
import threading

sys.path.append('../')  # Adjust the path as needed based on your project structure

from python_server.modes import clock_and_weather, news, weather_detail, football, stock_market
from python_server.shared.controller.matrix_controller import stop_scrolling_text
from python_server.shared.constants import *
from python_server.modes.clock_and_weather import stop_clock

# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configure CherryPy to listen on a specific host (e.g., 192.168.1.143)
cherrypy.config.update({'server.socket_host': '192.168.1.143'})

MODES = {
    0: {"name": "News (ANSA)", "run_function": news.run, "args": (ANSA_RSS_FEED_URL,)},
    1: {"name": "News (BalkanWeb)", "run_function": news.run, "args": (BALLKANWEB_RSS_FEED_URL,)},
    2: {"name": "News (Lapsi)", "run_function": news.run, "args": (LAPSI_RSS_FEED_URL,)},
    3: {"name": "Clock and Weather", "run_function": clock_and_weather.run, "args": ()},
    4: {"name": "Weather Detail", "run_function": weather_detail.run, "args": ()},
    5: {"name": "Football", "run_function": football.run, "args": ()},
    6: {"name": "Stock Market", "run_function": stock_market.run, "args": ()},
}

TOTAL_NUMBER_OF_MODES = len(MODES)
DEFAULT_MODE = MODES[3]  # Clock and Weather as default mode

class LEDMatrixDisplayService:
    def __init__(self):
        self.current_mode = 0  # Initialize the current mode
        self.current_thread = None  # Initialize the current running thread
        self.stop_event = threading.Event()  # Event to signal stopping the current mode
        # Start the default mode
        self.run_default_mode()

    def run_default_mode(self):
        self.stop_event.clear()
        mode_info = DEFAULT_MODE
        self.current_thread = threading.Thread(
            target=self.run_mode,
            args=(mode_info["run_function"], mode_info.get("args", ()))
        )
        self.current_thread.start()

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
                target=self.run_mode,
                args=(mode_info["run_function"], mode_info.get("args", ()))
            )
            self.current_thread.start()
            return {"message": f"Mode {mode} ({mode_info['name']}) started"}
        except KeyError:
            return {"message": "Invalid mode"}

    def run_mode(self, run_function, args):
        run_function(*args, self.stop_event)
        # After the mode finishes, run the default mode
        self.run_default_mode()

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