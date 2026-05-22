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
    logging.warning("[Cyberpunk Mode] rgbmatrix library not found. Running in SIMULATION mode.")

# Attempt to import weather service for dynamic weather integration
try:
    from python_server.shared.service.weather_service import get_weather_rome
    HAS_WEATHER_SERVICE = True
except ImportError:
    HAS_WEATHER_SERVICE = False

# --- Color Definitions ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 220, 255)
MAGENTA = (255, 0, 180)
NEON_BLUE = (0, 80, 255)
DARK_BLUE = (10, 8, 30)
INDIGO_BG = (20, 15, 45)
GRAY_FG = (35, 30, 42)
LIGHT_GRAY = (150, 150, 160)
DARK_GRAY = (60, 60, 70)
AMBER = (255, 140, 0)

# --- Neon Ad Sign: "ROMA" ---
NEON_AD_SPRITE = [
    "RRR   OOO  M   M   A  ",
    "R  R O   O MM MM  A A ",
    "RRR  O   O M M M AAAAA",
    "R R  O   O M   M A   A",
    "R  R  OOO  M   M A   A"
]

def draw_string_custom(draw, x, y, text_lines, color):
    for row_idx, line in enumerate(text_lines):
        for col_idx, char in enumerate(line):
            if char != ' ':
                draw.point((x + col_idx, y + row_idx), fill=color)

def run(stop_event):
    logging.info("[Cyberpunk Mode] Starting Cozy Cyberpunk City dynamic screensaver...")

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
            logging.error(f"[Cyberpunk Mode] Failed to initialize RGBMatrix: {e}")

    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # 1. Parallax Layers Data Structure
    # Infinite wrap width: virtual canvas width of 80 pixels
    bg_buildings = [
        {"x": 0.0, "w": 14, "h": 20, "color": (15, 10, 32)},
        {"x": 18.0, "w": 12, "h": 25, "color": (20, 12, 38)},
        {"x": 34.0, "w": 16, "h": 18, "color": (15, 10, 32)},
        {"x": 54.0, "w": 12, "h": 22, "color": (20, 12, 38)},
        {"x": 70.0, "w": 15, "h": 16, "color": (15, 10, 32)},
    ]

    fg_buildings = [
        {"x": 4.0, "w": 16, "h": 15, "color": (32, 28, 42), "accent": CYAN},
        {"x": 26.0, "w": 12, "h": 21, "color": (26, 22, 36), "accent": MAGENTA},
        {"x": 44.0, "w": 18, "h": 13, "color": (32, 28, 42), "accent": CYAN},
        {"x": 68.0, "w": 14, "h": 17, "color": (26, 22, 36), "accent": MAGENTA},
    ]

    # Initialize Rain Particles (used in Rain mode)
    num_drops = 16
    rain_drops = []
    for _ in range(num_drops):
        rain_drops.append({
            "x": random.uniform(-10, 70),
            "y": random.uniform(-5, 0),
            "speed": 1.5 + 1.2 * random.random()
        })
    active_splashes = []

    # Initialize Twinkling Stars (used in Clear mode)
    num_stars = 10
    stars = []
    for _ in range(num_stars):
        stars.append({
            "x": random.randint(0, 63),
            "y": random.randint(0, 10),
            "offset": random.random() * math.pi
        })
    shooting_star = {"x": -10.0, "y": -10.0, "vx": 3.0, "vy": 1.5, "active": False}

    # Initialize Clouds (used in Cloudy mode)
    clouds = [
        {"x": 5.0, "y": 2.0, "w": 16, "speed": 0.05},
        {"x": 40.0, "y": 4.0, "w": 20, "speed": 0.03}
    ]

    last_weather_fetch = 0
    weather_condition = "rain"  # Fallback weather

    try:
        while not stop_event.is_set():
            current_time = time.time()

            # --- Sincronizzazione Meteo Reale (ogni 5 minuti) ---
            if HAS_WEATHER_SERVICE and (current_time - last_weather_fetch > 300.0 or last_weather_fetch == 0):
                try:
                    logging.info("[Cyberpunk Mode] Fetching real-time weather from OpenWeatherMap...")
                    weather_data = get_weather_rome()
                    if isinstance(weather_data, dict) and "weather" in weather_data:
                        raw_cond = weather_data["weather"][0]["main"].lower()
                        if "rain" in raw_cond or "drizzle" in raw_cond or "thunderstorm" in raw_cond:
                            weather_condition = "rain"
                        elif "cloud" in raw_cond or "mist" in raw_cond or "fog" in raw_cond or "haze" in raw_cond:
                            weather_condition = "clouds"
                        elif "clear" in raw_cond:
                            weather_condition = "clear"
                        else:
                            weather_condition = "rain" # fallback visual
                        logging.info(f"[Cyberpunk Mode] Active weather condition registered: '{weather_condition}'")
                except Exception as e:
                    logging.warning(f"[Cyberpunk Mode] Failed to fetch weather, using cozy rain fallback: {e}")
                    weather_condition = "rain"
                last_weather_fetch = current_time

            # 1. Background sky render
            if weather_condition == "rain":
                # Dark rain clouds sky gradient
                draw.rectangle((0, 0, 63, 31), fill=(5, 3, 15))
            elif weather_condition == "clear":
                # Starry night sky gradient
                draw.rectangle((0, 0, 63, 31), fill=(4, 2, 22))
            else:
                # Cloudy foggy sky
                draw.rectangle((0, 0, 63, 31), fill=(12, 10, 24))

            # 2. Render Sky Elements (Stars, Clouds, Shooting Star)
            if weather_condition == "clear":
                # Draw stars
                t = time.time()
                for star in stars:
                    bright = int(100 + 155 * math.sin(t * 4.0 + star["offset"]))
                    draw.point((star["x"], star["y"]), fill=(bright, bright, int(bright * 0.9)))
                
                # Update & Draw Shooting Star
                if not shooting_star["active"] and random.randint(0, 150) == 1:
                    shooting_star["active"] = True
                    shooting_star["x"] = random.randint(0, 30)
                    shooting_star["y"] = 0
                
                if shooting_star["active"]:
                    sx, sy = int(shooting_star["x"]), int(shooting_star["y"])
                    # Draw tail
                    draw.line((sx, sy, sx - 4, sy - 2), fill=LIGHT_GRAY)
                    draw.point((sx, sy), fill=WHITE)
                    shooting_star["x"] += shooting_star["vx"]
                    shooting_star["y"] += shooting_star["vy"]
                    if shooting_star["x"] > 70 or shooting_star["y"] > 15:
                        shooting_star["active"] = False

            elif weather_condition == "clouds":
                # Draw clouds passing
                for cloud in clouds:
                    cx = int(cloud["x"])
                    cy = int(cloud["y"])
                    cw = cloud["w"]
                    # Draw cloud bubble shape
                    draw.ellipse((cx, cy, cx + cw, cy + 5), fill=(40, 35, 60))
                    draw.ellipse((cx + 3, cy - 2, cx + cw - 3, cy + 4), fill=(48, 43, 68))
                    cloud["x"] += cloud["speed"]
                    if cloud["x"] > 68:
                        cloud["x"] = -cw

            # 3. Update & Draw Parallax Skyscrapers
            # Background Layer Scrolling
            for b in bg_buildings:
                b["x"] -= 0.08
                if b["x"] + b["w"] < 0:
                    b["x"] += 80.0
                bx = int(b["x"])
                draw.rectangle((bx, 31 - b["h"], bx + b["w"], 30), fill=b["color"])
                
                # Draw sparse static windows in the background
                random.seed(bx)  # Consistent windows per building
                win_color = (60, 50, 20)
                for wx in range(bx + 2, bx + b["w"] - 2, 4):
                    for wy in range(31 - b["h"] + 2, 28, 6):
                        if random.random() > 0.6:
                            draw.point((wx, wy), fill=win_color)

            # Foreground Layer Scrolling
            # Pre-compute a 64-column height map of the foreground skyline for rain collision
            heightmap = [31] * 64

            for b in fg_buildings:
                b["x"] -= 0.25
                if b["x"] + b["w"] < 0:
                    b["x"] += 80.0
                bx = int(b["x"])
                
                # Draw Building Shadow
                draw.rectangle((bx, 31 - b["h"], bx + b["w"], 30), fill=b["color"], outline=DARK_GRAY)
                
                # Fill heights map
                start_col = max(0, bx)
                end_col = min(63, bx + b["w"])
                top_y = 31 - b["h"]
                for col in range(start_col, end_col):
                    if top_y < heightmap[col]:
                        heightmap[col] = top_y

                # Draw glowing windows
                random.seed(bx + 10)
                accent = b["accent"]
                for wx in range(bx + 2, bx + b["w"] - 2, 4):
                    for wy in range(31 - b["h"] + 3, 29, 5):
                        if random.random() > 0.4:
                            # 30% chance window is active neon
                            w_color = accent if random.random() > 0.7 else (80, 80, 80)
                            draw.rectangle((wx, wy, wx + 1, wy + 1), fill=w_color)

                # Special feature: Add a pulsing neon ad sign "ROMA" on building 2
                if b["accent"] == MAGENTA and bx >= -20 and bx <= 64:
                    # Pulsing amber color
                    pulse_val = int(140 + 115 * math.sin(current_time * 6.0))
                    ad_color = (pulse_val, int(pulse_val * 0.5), 0)
                    draw_string_custom(draw, bx - 2, 31 - b["h"] - 7, NEON_AD_SPRITE, ad_color)

            # Draw Ground Line (Horizon overlay at the bottom)
            draw.line((0, 31, 63, 31), fill=DARK_GRAY)

            # 4. Render Weather Mechanics (Rain Particles and Splashes)
            if weather_condition == "rain":
                # Update and Draw Rain
                for drop in rain_drops:
                    drop["x"] -= 0.6
                    drop["y"] += drop["speed"]

                    dx, dy = int(drop["x"]), int(drop["y"])
                    
                    # Wrap left/bottom edges
                    if dx < -2 or dy > 31:
                        drop["x"] = random.uniform(0, 75)
                        drop["y"] = -3
                        continue

                    # Collision with foreground building rooftops
                    if 0 <= dx < 64:
                        collision_y = heightmap[dx]
                        if dy >= collision_y:
                            # Add a splash at the collision height
                            active_splashes.append({
                                "x": dx,
                                "y": collision_y,
                                "frame": 0
                            })
                            # Reset raindrop
                            drop["x"] = random.uniform(0, 75)
                            drop["y"] = -3
                            continue
                    
                    # Draw diagonal drop line
                    draw.line((dx, dy, dx - 1, dy + 2), fill=(0, 160, 255))

                # Update & Draw Splashes
                next_splashes = []
                for splash in active_splashes:
                    sx, sy = splash["x"], splash["y"]
                    f = splash["frame"]
                    
                    if f == 0:
                        # Tiny single point splash
                        draw.point((sx, sy - 1), fill=CYAN)
                        splash["frame"] += 1
                        next_splashes.append(splash)
                    elif f == 1:
                        # Horizontal split splash
                        draw.point((sx - 1, sy - 1), fill=CYAN)
                        draw.point((sx + 1, sy - 1), fill=CYAN)
                        splash["frame"] += 1
                        next_splashes.append(splash)
                    # Frame 2 is deleted
                active_splashes = next_splashes

            # Update Display Canvas
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)

            # Framerate ~18 FPS (55ms sleep)
            time.sleep(0.055)

    except KeyboardInterrupt:
        logging.info("[Cyberpunk Mode] Exiting via keyboard interrupt.")
    finally:
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        logging.info("[Cyberpunk Mode] Stopped Cozy Cyberpunk City screensaver cleanly.")

if __name__ == "__main__":
    import threading
    logging.basicConfig(level=logging.INFO)
    stop_event = threading.Event()
    try:
        run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
