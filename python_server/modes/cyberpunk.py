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
        {"x": 4.0, "w": 20, "h": 13, "color": (25, 20, 35), "accent": CYAN, "type": "colosseum"},
        {"x": 28.0, "w": 12, "h": 21, "color": (26, 22, 36), "accent": MAGENTA, "type": "standard"},
        {"x": 46.0, "w": 18, "h": 13, "color": (32, 28, 42), "accent": CYAN, "type": "standard"},
        {"x": 68.0, "w": 14, "h": 17, "color": (26, 22, 36), "accent": MAGENTA, "type": "roma_sign"},
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
        {"x": 5.0, "y": 2.0, "w": 16, "speed": 0.04},
        {"x": 22.0, "y": 5.0, "w": 12, "speed": 0.06},
        {"x": 40.0, "y": 1.0, "w": 18, "speed": 0.03},
        {"x": 58.0, "y": 4.0, "w": 14, "speed": 0.05}
    ]

    last_weather_fetch = 0
    weather_condition = "rain"  # Fallback weather
    is_day = True # Fallback day status

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
                        
                        # Detect day/night from weather data
                        dt = weather_data.get("dt")
                        sys_data = weather_data.get("sys", {})
                        sunrise = sys_data.get("sunrise")
                        sunset = sys_data.get("sunset")
                        if dt and sunrise and sunset:
                            is_day = (sunrise <= dt <= sunset)
                        else:
                            hour = time.localtime().tm_hour
                            is_day = (6 <= hour < 20)
                except Exception as e:
                    logging.warning(f"[Cyberpunk Mode] Failed to fetch weather, using cozy rain fallback: {e}")
                    weather_condition = "rain"
                    hour = time.localtime().tm_hour
                    is_day = (6 <= hour < 20)
                last_weather_fetch = current_time

            # Fallback update day/night status based on local time if weather service not used
            if not HAS_WEATHER_SERVICE:
                hour = time.localtime().tm_hour
                is_day = (6 <= hour < 20)

            # 1. Background sky render based on day/night and weather conditions
            if is_day:
                if weather_condition == "rain":
                    # Moody rainy day sky (grayish blue-cyan)
                    draw.rectangle((0, 0, 63, 31), fill=(22, 28, 42))
                elif weather_condition == "clear":
                    # Vibrant cyberpunk day sky (bright neon-tinted cyan-blue)
                    draw.rectangle((0, 0, 63, 31), fill=(15, 75, 120))
                else:
                    # Cloudy foggy day sky (misty light blue-gray)
                    draw.rectangle((0, 0, 63, 31), fill=(35, 50, 75))
            else:
                if weather_condition == "rain":
                    # Dark rain clouds sky gradient
                    draw.rectangle((0, 0, 63, 31), fill=(5, 3, 15))
                elif weather_condition == "clear":
                    # Starry night sky gradient
                    draw.rectangle((0, 0, 63, 31), fill=(4, 2, 22))
                else:
                    # Cloudy foggy sky
                    draw.rectangle((0, 0, 63, 31), fill=(12, 10, 24))

            # 2. Render Sky Elements (Cyber-Sun, Twinkling Stars, Passing Clouds, Shooting Stars)
            if is_day:
                if weather_condition == "clear":
                    # Draw retro cyber-sun
                    cx, cy = 46, 8
                    # Outer glow (soft red-orange)
                    draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(180, 80, 0))
                    # Mid ring (bright orange)
                    draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(255, 130, 0))
                    # Bright core (yellowish white)
                    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(255, 230, 120))
            else:
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

            # Draw clouds passing if it is cloudy
            if weather_condition == "clouds":
                for cloud in clouds:
                    cx = int(cloud["x"])
                    cy = int(cloud["y"])
                    cw = cloud["w"]
                    
                    # Select cloud color based on day/night
                    if is_day:
                        c_fill1 = (95, 115, 135)
                        c_fill2 = (120, 140, 160)
                    else:
                        c_fill1 = (40, 35, 60)
                        c_fill2 = (48, 43, 68)
                        
                    # Draw cloud bubble shape
                    draw.ellipse((cx, cy, cx + cw, cy + 5), fill=c_fill1)
                    draw.ellipse((cx + 3, cy - 2, cx + cw - 3, cy + 4), fill=c_fill2)
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

            # Foreground Layer Scrolling & Rendering
            # Pre-compute a 64-column height map of the foreground skyline for rain collision
            heightmap = [31] * 64

            for b in fg_buildings:
                b["x"] -= 0.25
                if b["x"] + b["w"] < 0:
                    b["x"] += 80.0
                    
                    # Randomize building parameters upon wrapping to make the skyline procedural
                    rand_val = random.random()
                    if rand_val < 0.05:
                        b["type"] = "colosseum"
                        b["w"] = 20
                        b["h"] = 13
                        b["color"] = (25, 20, 35) # Sandstone shadow/fill base
                    elif rand_val < 0.10:
                        b["type"] = "roma_sign"
                        b["w"] = random.randint(14, 18)
                        b["h"] = random.randint(15, 22)
                        b["color"] = random.choice([(32, 28, 42), (26, 22, 36)])
                        b["accent"] = MAGENTA
                    else:
                        b["type"] = "standard"
                        b["w"] = random.randint(12, 18)
                        b["h"] = random.randint(12, 22)
                        b["color"] = random.choice([(32, 28, 42), (26, 22, 36)])
                        b["accent"] = random.choice([CYAN, MAGENTA, NEON_BLUE])
                
                bx = int(b["x"])
                b_type = b.get("type", "standard")

                if b_type == "colosseum":
                    # 1. Fill heights map for Colosseum's stepped roofline
                    for dx_offset in range(b["w"]):
                        col = bx + dx_offset
                        if 0 <= col < 64:
                            if dx_offset < 8:
                                top_y = 31 - b["h"]
                            elif dx_offset < 14:
                                top_y = 31 - (b["h"] - 2)
                            else:
                                top_y = 31 - (b["h"] - 4)
                            
                            if top_y < heightmap[col]:
                                heightmap[col] = top_y

                    # 2. Draw Sandstone Shadow Fill for the sections
                    # Left section (dx from 0 to 7)
                    draw.rectangle((bx, 31 - b["h"], bx + 7, 30), fill=(25, 20, 35))
                    # Middle section (dx from 8 to 13)
                    draw.rectangle((bx + 8, 31 - (b["h"] - 2), bx + 13, 30), fill=(25, 20, 35))
                    # Right section (dx from 14 to 19)
                    draw.rectangle((bx + 14, 31 - (b["h"] - 4), bx + 19, 30), fill=(25, 20, 35))

                    # 3. Draw Sandstone Outlines/Highlights
                    highlight_color = (180, 150, 110)
                    # Top outlines
                    draw.line((bx, 31 - b["h"], bx + 7, 31 - b["h"]), fill=highlight_color)
                    draw.line((bx + 8, 31 - (b["h"] - 2), bx + 13, 31 - (b["h"] - 2)), fill=highlight_color)
                    draw.line((bx + 14, 31 - (b["h"] - 4), bx + 19, 31 - (b["h"] - 4)), fill=highlight_color)

                    # Step vertical lines
                    draw.line((bx + 8, 31 - b["h"], bx + 8, 31 - (b["h"] - 2)), fill=highlight_color)
                    draw.line((bx + 14, 31 - (b["h"] - 2), bx + 14, 31 - (b["h"] - 4)), fill=highlight_color)

                    # Left and right outer walls
                    draw.line((bx, 31 - b["h"], bx, 30), fill=highlight_color)
                    draw.line((bx + 19, 31 - (b["h"] - 4), bx + 19, 30), fill=highlight_color)

                    # 4. Draw Arches, Torches, and Neons
                    # Bottom tier arches (at dx = 2, 6, 10, 14, 17)
                    bottom_arch_dxs = [2, 6, 10, 14, 17]
                    for dx in bottom_arch_dxs:
                        ax = bx + dx
                        # Fill arch interior with dark shadow
                        draw.rectangle((ax, 26, ax + 1, 29), fill=(10, 8, 20))
                        # Highlight arch frame with slightly lighter sandstone/gray
                        draw.point((ax, 25), fill=(80, 70, 55))
                        draw.point((ax + 1, 25), fill=(80, 70, 55))
                        
                        # Glowing amber torch inside the arch (pulsing flame)
                        torch_pulse = int(180 + 75 * math.sin(current_time * 8.0 + dx))
                        torch_color = (torch_pulse, int(torch_pulse * 0.55), 0)
                        # We use a semi-random but stable choice for which pixel lights up
                        draw.point((ax + (1 if (int(current_time * 4) + dx) % 2 == 0 else 0), 27), fill=torch_color)

                    # Top tier arches (where they fit: dx = 2, 6, 10)
                    top_arch_specs = [
                        {"dx": 2, "y1": 21, "y2": 24},
                        {"dx": 6, "y1": 21, "y2": 24},
                        {"dx": 10, "y1": 22, "y2": 24}
                    ]
                    for spec in top_arch_specs:
                        dx = spec["dx"]
                        y1 = spec["y1"]
                        y2 = spec["y2"]
                        ax = bx + dx
                        # Fill top arch interior
                        draw.rectangle((ax, y1, ax + 1, y2), fill=(10, 8, 20))
                        # Glowing cyan neon
                        neon_pulse = int(180 + 75 * math.sin(current_time * 5.0 + dx))
                        neon_color = (0, neon_pulse, neon_pulse)
                        draw.point((ax + 1, y1 + 1), fill=neon_color)

                else:
                    # standard or roma_sign
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
                    accent = b.get("accent", CYAN)
                    for wx in range(bx + 2, bx + b["w"] - 2, 4):
                        for wy in range(31 - b["h"] + 3, 29, 5):
                            if random.random() > 0.4:
                                # 30% chance window is active neon
                                w_color = accent if random.random() > 0.7 else (80, 80, 80)
                                draw.rectangle((wx, wy, wx + 1, wy + 1), fill=w_color)

                    # ROMA sign
                    if b_type == "roma_sign" and bx >= -22 and bx <= 64:
                        # Center the sign on top of the building
                        sign_x = bx + (b["w"] - 22) // 2
                        # Pulsing orange-amber color
                        pulse_val = int(140 + 115 * math.sin(current_time * 6.0))
                        ad_color = (pulse_val, int(pulse_val * 0.5), 0)
                        draw_string_custom(draw, sign_x, 31 - b["h"] - 7, NEON_AD_SPRITE, ad_color)

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
