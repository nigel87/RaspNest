import time
import math
import random
import logging
from PIL import Image, ImageDraw

# Try importing the rgbmatrix library. Fall back to simulation if not on Raspberry Pi.
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logging.warning("[Outrun Mode] rgbmatrix library not found. Running in SIMULATION mode.")

# --- Color Definitions ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_PINK = (255, 0, 128)
NEON_PURPLE = (180, 0, 255)
SUN_YELLOW = (255, 215, 0)
SUN_ORANGE = (255, 69, 0)
SUN_RED = (255, 0, 50)
CYAN = (0, 255, 255)
DARK_GRAY = (40, 40, 40)
STARS_COLOR = (240, 240, 255)

# --- Retro Sports Car Sprite (Seen from behind, 12x6) ---
CAR_SPRITE = [
    "   CCCC   ",  # Row 0: Glass Canopy (C = Cyan)
    "  RRRRRR  ",  # Row 1: Upper body (R = Red)
    " RRRRRRRR ",  # Row 2: Mid body
    "YRRRRRRY  ",  # Row 3: Blinkers & tail lights (Y = Yellow/Amber)
    "LLKKKKLL  ",  # Row 4: Bright red tail-lights (L = Neon Red) & Exhaust
    "  K  K    "   # Row 5: Wheels (K = Black/Dark Gray)
]

CAR_COLOR_MAP = {
    'C': (0, 190, 255),
    'R': (255, 10, 50),
    'Y': (255, 165, 0),
    'L': (255, 0, 0),
    'K': (25, 25, 25)
}

def draw_sprite(draw, x, y, sprite_lines, color_map):
    for row_idx, line in enumerate(sprite_lines):
        for col_idx, char in enumerate(line):
            if char != ' ' and char in color_map:
                draw.point((x + col_idx, y + row_idx), fill=color_map[char])

def run(stop_event):
    logging.info("[Outrun Mode] Starting Outrun / Retro Wave Highway screensaver...")

    # Initialize the LED Matrix if available
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
            logging.error(f"[Outrun Mode] Failed to initialize RGBMatrix: {e}")

    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Initialize dynamic stars
    num_stars = 8
    stars = []
    for _ in range(num_stars):
        stars.append({
            "x": random.randint(0, 63),
            "y": random.randint(0, 15),
            "speed": 0.05 + 0.1 * random.random(),
            "offset": random.random() * math.pi
        })

    # Perspective horizontal line y-positions
    y_lines = [17.0, 18.5, 20.5, 23.0, 26.5, 31.0]

    # Main animation loop
    try:
        while not stop_event.is_set():
            # 1. Clear background
            draw.rectangle((0, 0, width, height), fill=BLACK)

            # 2. Draw Twinkling Stars
            t = time.time()
            for star in stars:
                brightness = int(127 + 128 * math.sin(t * 8.0 * star["speed"] + star["offset"]))
                star_color = (brightness, brightness, int(brightness * 1.1))
                draw.point((star["x"], star["y"]), fill=star_color)

            # 3. Draw Sliced Retro Sunset
            # Sun Center: (32, 13), radius: 10
            sun_cx, sun_cy = 32, 13
            sun_r = 10
            for sy in range(sun_cy - sun_r, sun_cy + sun_r + 1):
                # Calculate horizontal span of the circle at this y
                dy = abs(sy - sun_cy)
                dx = int(math.sqrt(max(0, sun_r*sun_r - dy*dy)))
                
                # Check for retro sliced scanlines (skip lines with increasing thickness at the bottom)
                # Horizon is at y = 17, so lines closer to 17 have thicker black bars
                slice_gap = False
                if sy == 16:
                    slice_gap = True
                elif sy == 14:
                    slice_gap = True
                elif sy == 11:
                    slice_gap = True
                elif sy == 7:
                    slice_gap = True

                if slice_gap:
                    continue

                # Calculate color gradient (yellow at top, magenta/red at bottom)
                ratio = (sy - (sun_cy - sun_r)) / (2.0 * sun_r)
                # Linear blend between SUN_YELLOW and SUN_RED
                r = int(SUN_YELLOW[0] + ratio * (SUN_RED[0] - SUN_YELLOW[0]))
                g = int(SUN_YELLOW[1] + ratio * (SUN_RED[1] - SUN_YELLOW[1]))
                b = int(SUN_YELLOW[2] + ratio * (SUN_RED[2] - SUN_YELLOW[2]))
                draw.line((sun_cx - dx, sy, sun_cx + dx, sy), fill=(r, g, b))

            # 4. Draw Neon Perspective Grid Lines
            # Horizon line (solid neon pink separator at y = 16)
            draw.line((0, 16, 63, 16), fill=NEON_PINK)

            # Draw vertical converging lines
            # Vanishing point is at (32, 16)
            grid_cols = [0, 8, 16, 24, 32, 40, 48, 56, 64]
            for bx in grid_cols:
                # Interpolate from horizon level (y=16) to bottom (y=31)
                draw.line((32, 16, bx, 31), fill=NEON_PURPLE)

            # Update and draw horizontal scrolling lines (accelerating towards bottom)
            for i in range(len(y_lines)):
                # Accelerate vertical displacement based on distance from horizon (16.0)
                y_lines[i] += 0.08 * (y_lines[i] - 15.5)
                # Wrap line if it goes past the matrix height (31)
                if y_lines[i] > 31.0:
                    y_lines[i] = 17.0

                # Render horizontal grid line
                draw.line((0, int(y_lines[i]), 63, int(y_lines[i])), fill=NEON_PURPLE)

            # 5. Draw Swaying Arcade Sports Car
            car_x = 26 + int(math.sin(t * 3.0) * 8.0) # Sway left and right
            car_y = 23
            draw_sprite(draw, car_x, car_y, CAR_SPRITE, CAR_COLOR_MAP)

            # Update Display Canvas
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)
            
            # Framerate ~20 FPS (50ms sleep)
            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("[Outrun Mode] Exiting via keyboard interrupt.")
    finally:
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        logging.info("[Outrun Mode] Stopped Outrun screensaver cleanly.")

if __name__ == "__main__":
    import threading
    logging.basicConfig(level=logging.INFO)
    stop_event = threading.Event()
    try:
        run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
