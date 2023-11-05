import cherrypy
import os
import subprocess
import sys

# Set the working directory to the project folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the project root directory to the Python path
project_root = os.path.dirname(__file__)
sys.path.append(project_root)

# Configure CherryPy to listen on a specific host (e.g., 192.168.1.143)
cherrypy.config.update({'server.socket_host': '192.168.1.143'})

class LEDMatrixDisplayService:
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def displayMessage(self):
        data = cherrypy.request.json
        mode = data.get('mode', 0)  # Default mode is 0
        text = data.get('text', 'Hello, World!')  # Default text

        # Define the folder containing the C++ binary
        cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')

        if mode == 0:
            cpp_binary = os.path.join(cpp_binary_folder, 'text-scroller')
            args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), text, '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat', '--led-slowdown-gpio=4']
        elif mode == 1:
            cpp_binary = os.path.join(cpp_binary_folder, 'your_other_program')  # Replace with your other C++ program
            args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), '03:11', '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat', '--led-slowdown-gpio=4']
        else:
            return {"message": "Invalid mode"}

        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as e:
            return {"message": f"Error executing program: {str(e)}"}

        return {"message": "OK"}

if __name__ == '__main__':
    cherrypy.quickstart(LEDMatrixDisplayService())

