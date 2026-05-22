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

    # Roadside perspective scaling objects (trees and buildings)
    roadside_objects = []

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

            # 3. Draw Solid Retro Sunset (Clipped at the horizon y = 16 for a clean look)
            # Sun Center: (32, 13), radius: 10
            sun_cx, sun_cy = 32, 13
            sun_r = 10
            for sy in range(sun_cy - sun_r, sun_cy + sun_r + 1):
                if sy >= 16:
                    continue  # Clip the bottom of the sun to sit perfectly behind the horizon
                
                # Calculate horizontal span of the circle at this y
                dy = abs(sy - sun_cy)
                dx = int(math.sqrt(max(0, sun_r*sun_r - dy*dy)))

                # Calculate color gradient (yellow at top, magenta/red at bottom)
                ratio = (sy - (sun_cy - sun_r)) / (2.0 * sun_r)
                # Linear blend between SUN_YELLOW and SUN_RED
                r = int(SUN_YELLOW[0] + ratio * (SUN_RED[0] - SUN_YELLOW[0]))
                g = int(SUN_YELLOW[1] + ratio * (SUN_RED[1] - SUN_YELLOW[1]))
                b = int(SUN_YELLOW[2] + ratio * (SUN_RED[2] - SUN_YELLOW[2]))
                draw.line((sun_cx - dx, sy, sun_cx + dx, sy), fill=(r, g, b))

            # 4. Draw Neon Perspective Grid Lines (Horizon line separator removed for seamless layout)
            # Draw vertical converging lines
            # Vanishing point is at (32, 16)
            grid_cols = [0, 8, 16, 24, 32, 40, 48, 56, 64]
            for bx in grid_cols:
                # Interpolate from horizon level (y=16) to bottom (y=31)
                draw.line((32, 16, bx, 31), fill=NEON_PURPLE)

            # 4b. Spawn, Update and Draw 3D Perspective Roadside Objects (Trees and Buildings)
            if len(roadside_objects) < 3 and random.random() < 0.15:
                can_spawn = True
                if roadside_objects:
                    last_obj = roadside_objects[-1]
                    if last_obj["z"] > 0.75:
                        can_spawn = False
                if can_spawn:
                    roadside_objects.append({
                        "side": random.choice(["left", "right"]),
                        "type": random.choice(["tree", "building"]),
                        "z": 1.0,
                        "color_theme": random.choice(["cyan", "magenta"])
                    })
            
            # Sort back-to-front so closer objects overlap distant ones correctly
            roadside_objects.sort(key=lambda o: o["z"], reverse=True)
            
            next_objects = []
            for obj in roadside_objects:
                obj["z"] -= 0.045  # Speed of approaching objects
                if obj["z"] <= 0.08:
                    continue  # Passed the viewer, recycle
                
                z = obj["z"]
                progress = 1.0 - z
                
                if obj["side"] == "left":
                    cx = int(32 - 34 * progress)
                else:
                    cx = int(32 + 34 * progress)
                    
                cy = int(16 + 15 * progress)
                
                # Scale coordinates dynamically based on 3D depth
                h = int(2 + 12 * progress)
                w = int(1 + 7 * progress)
                
                if cx < -10 or cx > 74 or cy > 32:
                    continue
                
                if obj["type"] == "tree":
                    trunk_color = NEON_PINK if obj["color_theme"] == "magenta" else (180, 0, 255)
                    leaf_color = CYAN if obj["color_theme"] == "cyan" else (0, 255, 80)
                    
                    # Draw curves trunk
                    for i in range(h):
                        ty = cy - i
                        tx = cx - int(math.sin(i / max(1, h) * 1.5) * (w / 3.0))
                        if 0 <= tx < 64 and 0 <= ty < 32:
                            draw.point((tx, ty), fill=trunk_color)
                            
                    # Draw leaves spread
                    top_y = cy - h
                    top_x = cx - int(math.sin(1.5) * (w / 3.0))
                    if w >= 2:
                        half_w = max(1, w // 2)
                        for lx in range(top_x - half_w, top_x + half_w + 1):
                            if 0 <= lx < 64 and 0 <= top_y < 32:
                                draw.point((lx, top_y), fill=leaf_color)
                        for ly in range(top_y - half_w // 2, top_y + half_w // 2 + 1):
                            if 0 <= top_x < 64 and 0 <= ly < 32:
                                draw.point((top_x, ly), fill=leaf_color)
                else:
                    # Draw perspective skyscraper building
                    building_color = (12, 8, 30)
                    border_color = CYAN if obj["color_theme"] == "cyan" else NEON_PINK
                    
                    bx1 = cx - w // 2
                    bx2 = cx + w // 2
                    by1 = cy - h
                    by2 = cy
                    
                    draw.rectangle((bx1, by1, bx2, by2), fill=building_color, outline=border_color)
                    
                    # Sparse glowing windows
                    if w >= 4 and h >= 6:
                        win_y = cy - h // 2
                        if 0 <= cx < 64 and 0 <= win_y < 32:
                            draw.point((cx, win_y), fill=(255, 220, 0))
                        if w >= 6 and h >= 8:
                            win_y2 = cy - h // 3
                            if 0 <= cx - 1 < 64 and 0 <= win_y2 < 32:
                                draw.point((cx - 1, win_y2), fill=(255, 220, 0))
                            if 0 <= cx + 1 < 64 and 0 <= win_y2 < 32:
                                draw.point((cx + 1, win_y2), fill=(255, 220, 0))
                                
                next_objects.append(obj)
            roadside_objects = next_objects

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
