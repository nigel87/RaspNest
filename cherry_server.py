import cherrypy
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import json

# Configuration for the LED matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options=options)


class LEDMatrixDisplayService:
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def displayMessage(self):
        data = cherrypy.request.json
        message = "Hello, World!" if data.get('mode') == 1 else "Ciao, World!"

        # Create a blank image with the same size as the LED matrix
        image = Image.new("RGB", (options.cols, options.rows))
        draw = ImageDraw.Draw(image)

        # Load a font (you can change the font and size as needed)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)

        # Display text
        draw.text((2, 10), message, fill=(255, 0, 0), font=font)

        # Convert the image to RGBMatrix format
        matrix.SetImage(image)

        return {"message": "OK"}



cherrypy.config.update({'server.socket_host': '192.168.1.143'})

if __name__ == '__main__':
    cherrypy.quickstart(LEDMatrixDisplayService())