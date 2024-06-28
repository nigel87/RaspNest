from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont
import time

def display_text(text, duration=5):
    print("start display text")
    # Configuration for the LED matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'

    matrix = RGBMatrix(options=options)

    # Create a blank image with the same size as the LED matrix
    image = Image.new("RGB", (options.cols, options.rows))
    draw = ImageDraw.Draw(image)

    # Load a font (you can change the font and size as needed)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)

    # Display text
    draw.text((2, 10), text, fill=(255, 0, 0), font=font)

    # Convert the image to RGBMatrix format
    matrix.SetImage(image)

    # Sleep to keep the text displayed for the specified duration
    time.sleep(duration)

    print("exit display text")




def scroll_text(text, duration=5):
    print("start scroll text")
    # Configuration for the LED matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'

    matrix = RGBMatrix(options=options)

    # Create a blank image with a wider canvas for scrolling
    image = Image.new("RGB", (options.cols * 2, options.rows))
    draw = ImageDraw.Draw(image)

    # Load a font (you can change the font and size as needed)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)

    # Calculate the width of the text
    text_width, text_height = draw.textsize(text, font=font)

    # Initialize the starting position of the viewport
    viewport_x = 0

    # Calculate the maximum viewport_x position for scrolling
    max_scroll = text_width - options.cols

    # Scroll the text from right to left
    while viewport_x <= max_scroll:
        draw.rectangle(((0, 0), (options.cols * 2, options.rows)), fill=(0, 0, 0))
        draw.text((options.cols - viewport_x, 10), text, fill=(255, 0, 0), font=font)
        viewport = image.crop((viewport_x, 0, viewport_x + options.cols, options.rows))
        matrix.SetImage(viewport)
        time.sleep(0.05)  # Adjust the speed of scrolling here
        viewport_x += 1

    # Sleep to keep the text displayed for the specified duration
    time.sleep(duration)

    print("exit scroll text")


def scroll_text_infinite(text, scroll_speed=0.05):
        print("start infinite scroll text")
        # Configuration for the LED matrix
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat'

        matrix = RGBMatrix(options=options)

        offscreen_canvas = matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("7x13.bdf")
        textColor = graphics.Color(255, 0, 0)
        pos = offscreen_canvas.width
        my_text = text

        while True:
            offscreen_canvas.Clear()
            len = graphics.DrawText(offscreen_canvas, font, pos, 10, textColor, my_text)
            pos -= 1
            if (pos + len < 0):
                pos = offscreen_canvas.width

            time.sleep(scroll_speed)
            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)


def display_text_infinite(text, duration=5):
    print("start display text")

    # Configuration for the LED matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'

    matrix = RGBMatrix(options=options)

    # Load a font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)

    # Get the size of the text
    size = font.getsize(text)

    pos = matrix.width  # Initial position off the right side of the display

    try:
        while True:
            offscreen_canvas = matrix.SwapOnVSync(matrix.CreateFrameCanvas())

            # Clear the canvas
            offscreen_canvas.Clear()

            # Create a blank image with the same size as the LED matrix
            image = Image.new("RGB", (size[0], matrix.height))
            draw = ImageDraw.Draw(image)

            # Draw the text at the current position
            draw.text((pos, 10), text, fill=(255, 0, 0), font=font)

            offscreen_canvas.SetImage(image)

            pos -= 1
            if pos + size[0] < 0:
                pos = matrix.width

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exiting")
        matrix.Clear()
        matrix.Update()
        return

if __name__ == '__main__':
    display_text("Hello, World!")




