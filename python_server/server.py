import sys
sys.path.append('../')
import os
import cherrypy
import threading

from modes import news, mode0
from scrolling_text_controller import stop_scrolling_text
from constants import *
# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the project root directory to the Python path
project_root = os.path.dirname(__file__)
sys.path.append(project_root)

# Configure CherryPy to listen on a specific host (e.g., 192.168.1.143)
cherrypy.config.update({'server.socket_host': '192.168.1.143'})
TOTAL_NUMBER_OF_MODES = 4

class LEDMatrixDisplayService:
    def __init__(self):
        self.current_mode = 0  # Initialize the current mode
        self.current_thread = None  # Initialize the current running thread
        self.stop_event = threading.Event()  # Event to signal stopping the current mode

    def start_mode_thread(self, mode, text, cpp_binary_folder):
        # Signal the current thread to stop and wait for it to finish
        if self.current_thread and self.current_thread.is_alive():
            self.stop_event.set()
            self.current_thread.join()

        # Reset the stop event for the new mode
        self.stop_event.clear()

        # Run the corresponding mode in a new thread
        
        if mode == 0:
            self.current_thread = threading.Thread(target=news.run, args=(ANSA_RSS_FEED_URL,cpp_binary_folder, self.stop_event))
        elif mode == 1:
            self.current_thread = threading.Thread(target=news.run, args=(BALLKANWEB_RSS_FEED_URL,cpp_binary_folder, self.stop_event))
        elif mode == 2:
            self.current_thread = threading.Thread(target=news.run, args=(LAPSI_RSS_FEED_URL,cpp_binary_folder, self.stop_event))
        elif mode == 3:
            self.current_thread = threading.Thread(target=mode0.run, args=(text, cpp_binary_folder))
        else:
            raise ValueError("Invalid mode")

        self.current_thread.start()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def display_message(self):
        data = cherrypy.request.json
        mode = data.get('mode', None)  # No default mode here to allow cycling
        text = data.get('text', 'Hello, World!')  # Default text

        # If no mode is specified, cycle to the next mode
        if mode is None:
            self.current_mode = (self.current_mode + 1) % TOTAL_NUMBER_OF_MODES  # Cycle through modes 0, 1, 2, 3
            mode = self.current_mode
        else:
            mode = int(mode)  # Ensure mode is an integer

        # Define the folder containing the C++ binary
        cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')

        # Start the mode thread
        self.start_mode_thread(mode, text, cpp_binary_folder)

        return {"message": f"Mode {mode} started"}

if __name__ == '__main__':
    cherrypy.quickstart(LEDMatrixDisplayService())