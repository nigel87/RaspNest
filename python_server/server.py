import sys
sys.path.append('../')
import os

from modes import mode0, mode1
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


class LEDMatrixDisplayService:

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def display_message(self):
        data = cherrypy.request.json
        mode = data.get('mode', 0)  # Default mode is 0
        text = data.get('text', 'Hello, World!')  # Default text

        # Call the function to stop scrolling text
        stop_scrolling_text()

        # Define the folder containing the C++ binary
        cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')

        if mode == 0:
            return mode0.run(text, cpp_binary_folder)
        elif mode == 1:
            return mode1.run(text, cpp_binary_folder)
        else:
            return {"message": "Invalid mode"}




if __name__ == '__main__':
    cherrypy.quickstart(LEDMatrixDisplayService())