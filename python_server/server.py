import sys
sys.path.append('../')
import os

from modes import ansa, ballkanweb, lapsi, mode0
from scrolling_text_controller import  stop_scrolling_text

# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the project root directory to the Python path
project_root = os.path.dirname(__file__)
sys.path.append(project_root)
# Import CherryPy after adding the modes directory to the Python path
import cherrypy
# Configure CherryPy to listen on a specific host (e.g., 192.168.1.143)
cherrypy.config.update({'server.socket_host': '192.168.1.143'})
TOTAL_NUMBER_OF_MODES = 4

class LEDMatrixDisplayService:
    def __init__(self):
        self.current_mode = 0  # Initialize the current mode

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def display_message(self):
        data = cherrypy.request.json
        mode = data.get('mode', 0)  # Default mode is 0
        text = data.get('text', 'Hello, World!')  # Default text

        # Call the function to stop scrolling text
        stop_scrolling_text()
        
        # If no mode is specified, cycle to the next mode
        if mode is None:
            self.current_mode = (self.current_mode + 1) % TOTAL_NUMBER_OF_MODES  # Cycle through modes 0, 1, 2
            mode = self.current_mode
        else:
            mode = int(mode)  # Ensure mode is an integer



        # Define the folder containing the C++ binary
        cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')

        if mode == 0:
            return ansa.run(cpp_binary_folder)
        elif mode == 1:
            return lapsi.run(cpp_binary_folder)
        elif mode == 2:
            return ballkanweb.run( cpp_binary_folder)
        elif mode == 3:
            return mode0.run(text, cpp_binary_folder)
        else:
            return {"message": "Invalid mode"}




if __name__ == '__main__':
    cherrypy.quickstart(LEDMatrixDisplayService())