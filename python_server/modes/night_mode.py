import time
import logging
from PIL import Image, ImageDraw

# Try importing the rgbmatrix library. Fall back to simulation if not on Raspberry Pi.
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logging.warning("[Night Mode] rgbmatrix library not found. Running in SIMULATION mode.")

FONT_5X7 = {
    '0': [
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        " ### "
    ],
    '1': [
        "  #  ",
        " ##  ",
        "  #  ",
        "  #  ",
        " ### "
    ],
    '2': [
        " ### ",
        "    #",
        " ### ",
        "#    ",
        " ### "
    ],
    '3': [
        " ### ",
        "    #",
        "  ## ",
        "    #",
        " ### "
    ],
    '4': [
        "#  # ",
        "#  # ",
        "#### ",
        "   # ",
        "   # "
    ],
    '5': [
        "#### ",
        "#    ",
        "###  ",
        "   # ",
        "###  "
    ],
    '6': [
        " ### ",
        "#    ",
        "#### ",
        "#   #",
        " ### "
    ],
    '7': [
        "#### ",
        "   # ",
        "  #  ",
        " #   ",
        " #   "
    ],
    '8': [
        " ### ",
        "#   #",
        " ### ",
        "#   #",
        " ### "
    ],
    '9': [
        " ### ",
        "#   #",
        " ####",
        "    #",
        " ### "
    ],
    ':': [
        " ",
        "#",
        " ",
        "#",
        " "
    ]
}

def draw_char_pixel_doubled(draw, x, y, char, color):
    lines = FONT_5X7.get(char, ["     "] * 5)
    for row_idx, line in enumerate(lines):
        for col_idx, pixel in enumerate(line):
            if pixel == '#':
                # Draw a 2x2 square for each pixel
                draw.rectangle((x + col_idx*2, y + row_idx*2, x + col_idx*2 + 1, y + row_idx*2 + 1), fill=color)

def run(stop_event):
    logging.info("[Night Mode] Starting Night Mode dim clock screensaver...")

    # Initialize LED Matrix if available
    matrix = None
    if HAS_MATRIX:
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat'
        options.gpio_slowdown = 4
        options.disable_hardware_pulsing = True
        options.drop_privileges = False
        try:
            matrix = RGBMatrix(options=options)
        except Exception as e:
            logging.error(f"[Night Mode] Failed to initialize RGBMatrix: {e}")

    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Ambient dim orange/amber color so it does not disturb at night
    glow_color = (60, 25, 0)

    try:
        while not stop_event.is_set():
            # Clear canvas to pure black
            draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

            # Fetch current local time
            now_struct = time.localtime()
            hh = f"{now_struct.tm_hour:02d}"
            mm = f"{now_struct.tm_min:02d}"

            # Colon flashes every second
            show_colon = int(time.time()) % 2 == 0

            # Draw time (50px wide, center aligned, x_start = 7, y_start = 11)
            x = 7
            y = 11

            # Digit 1 (Hour tens)
            draw_char_pixel_doubled(draw, x, y, hh[0], glow_color)
            x += 12

            # Digit 2 (Hour ones)
            draw_char_pixel_doubled(draw, x, y, hh[1], glow_color)
            x += 12

            # Pulsing Colon
            if show_colon:
                draw_char_pixel_doubled(draw, x, y, ':', glow_color)
            x += 4

            # Digit 3 (Minute tens)
            draw_char_pixel_doubled(draw, x, y, mm[0], glow_color)
            x += 12

            # Digit 4 (Minute ones)
            draw_char_pixel_doubled(draw, x, y, mm[1], glow_color)

            # Update Matrix display
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)

            # Sleep 100ms for responsiveness
            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("[Night Mode] Exiting via manual interrupt.")
    finally:
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        logging.info("[Night Mode] Stopped Night Mode clock screensaver cleanly.")
