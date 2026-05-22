import time
import math
import random
import logging
import queue
from PIL import Image, ImageDraw

# Try importing the rgbmatrix library. Fall back to simulation if not on Raspberry Pi.
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logging.warning("[Aquarium Mode] rgbmatrix library not found. Running in SIMULATION mode.")

# --- Thread-Safe Queue for Interactive Feeding ---
food_queue = queue.Queue()

# --- Visual Colors & Palettes ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PINK_HEART = (255, 100, 150)
GOLDEN_FOOD = (255, 200, 0)

# Colors for sprites mapping
COLOR_MAP = {
    'O': (255, 110, 0),    # Orange (Clownfish)
    'W': (240, 240, 240),  # White stripe
    'K': (20, 20, 20),      # Black eye/outline
    'B': (0, 90, 255),     # Royal Blue (Blue Tang)
    'Y': (255, 215, 0),    # Yellow (Blue Tang Tail)
    'P': (255, 130, 190),   # Pink (Jellyfish Bell)
    'T': (200, 160, 255),   # Soft Purple (Jellyfish Tentacles)
}

# --- Sprites Definition ---
# Clownfish (5x3)
CLOWNFISH_L = [
    " OOOO",
    "KWOWO",
    " OOOO"
]
CLOWNFISH_R = [
    "OOOO ",
    "OWOWK",
    "OOOO "
]

# Blue Tang (5x3)
BLUETANG_L = [
    " BBB ",
    "KBYYY",
    " BBB "
]
BLUETANG_R = [
    " BBB",
    "YYYBK",
    " BBB"
]

# Jellyfish (4x4)
JELLYFISH_PULSE = [
    " PPP ",
    "PPPPP",
    " T T ",
    " T T "
]
JELLYFISH_DRIFT = [
    " PPP ",
    "PPPPP",
    "T   T",
    "T   T"
]

class Fish:
    def __init__(self, fish_type, x, y, vx, vy):
        self.type = fish_type
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        
        # Dimensions
        if self.type == "jellyfish":
            self.width, self.height = 5, 4
        else:
            self.width, self.height = 5, 3
            
        self.state = "cruising"  # "cruising" or "hunting"
        self.target_food = None
        self.heart_timer = 0.0
        
        # Jellyfish specific variables
        self.pulse_timer = random.uniform(0, 3)
        self.pulse_state = 0  # 0 = relaxed/drifting, 1 = contracted/propelling

    def update(self, current_time, active_foods):
        # Apply Jellyfish vertical propulsion loop
        if self.type == "jellyfish":
            self.pulse_timer += 0.05
            if self.pulse_timer >= 3.0:
                self.pulse_timer = 0.0
                # Give a strong vertical upward impulse
                self.vy = -0.7 - random.uniform(0, 0.3)
                self.vx = random.uniform(-0.15, 0.15)
                self.pulse_state = 1  # contracted sprite
            else:
                # Gradual decelerating vertical drift down (water drag)
                self.vy += 0.025
                if self.vy > 0.15:
                    self.vy = 0.15  # terminal velocity down
                
                # Horizontal drift swaying
                self.vx = 0.1 * math.sin(current_time * 2.0)
                
                if self.vy > -0.1:
                    self.pulse_state = 0  # relaxed sprite
                    
            # Update positions
            self.x += self.vx
            self.y += self.vy
            
            # Boundary bounce
            if self.x < 2:
                self.x = 2
                self.vx = -self.vx
            elif self.x > 62 - self.width:
                self.x = 62 - self.width
                self.vx = -self.vx
                
            if self.y < 3:
                self.y = 3
                self.vy = 0.05
            elif self.y > 27 - self.height:
                self.y = 27 - self.height
                self.vy = -0.05
                
            return

        # Regular fish AI (Clownfish & Blue Tang)
        # 1. State check: Hunting or Cruising
        if self.state == "hunting" and (self.target_food not in active_foods or self.target_food is None):
            self.state = "cruising"
            self.target_food = None

        if self.state == "cruising" and active_foods:
            # Look for the nearest food flake
            nearest_food = None
            min_dist = 999.0
            for food in active_foods:
                dist = math.hypot(food["x"] - (self.x + 2), food["y"] - (self.y + 1))
                if dist < min_dist:
                    min_dist = dist
                    nearest_food = food
            if nearest_food and min_dist < 40.0:  # Sight range
                self.state = "hunting"
                self.target_food = nearest_food

        # 2. Velocity calculations based on state
        if self.state == "hunting" and self.target_food:
            fx, fy = self.target_food["x"], self.target_food["y"]
            dx = fx - (self.x + 2)
            dy = fy - (self.y + 1)
            dist = math.hypot(dx, dy)
            if dist > 0.5:
                # Steer towards food flake
                target_vx = (dx / dist) * 0.45
                target_vy = (dy / dist) * 0.35
            else:
                target_vx, target_vy = self.vx, self.vy
                
            # Soft steering interpolation
            self.vx = self.vx * 0.85 + target_vx * 0.15
            self.vy = self.vy * 0.85 + target_vy * 0.15
        else:
            # Cruising velocity
            # Maintain a horizontal movement with subtle sinusoids
            if self.type == "blue_tang":
                # Dory swims in sinusoids
                self.vy = 0.15 * math.sin(current_time * 2.5)
            else:
                # Nemo cruises horizontally with minimal height changes
                self.vy = self.vy * 0.9 + 0.05 * math.sin(current_time * 1.5)

            # Cap speeds
            max_vx = 0.35 if self.type == "blue_tang" else 0.25
            if abs(self.vx) < 0.05:
                self.vx = max_vx if random.random() > 0.5 else -max_vx
            
            # Keep cruising horizontal
            if self.vx > 0:
                self.vx = max_vx
            else:
                self.vx = -max_vx

        # 3. Position integration
        self.x += self.vx
        self.y += self.vy

        # 4. Boundary collisions and horizontal flips
        if self.x < 1:
            self.x = 1
            self.vx = abs(self.vx)  # Turn right
        elif self.x > 63 - self.width:
            self.x = 63 - self.width
            self.vx = -abs(self.vx)  # Turn left

        if self.y < 2:
            self.y = 2
            self.vy = abs(self.vy)
        elif self.y > 27 - self.height:  # Remain above seaweed bed
            self.y = 27 - self.height
            self.vy = -abs(self.vy)

    def draw(self, draw):
        # Select appropriate sprite
        if self.type == "jellyfish":
            sprite = JELLYFISH_PULSE if self.pulse_state == 1 else JELLYFISH_DRIFT
        elif self.vx >= 0:
            sprite = CLOWNFISH_R if self.type == "clownfish" else BLUETANG_R
        else:
            sprite = CLOWNFISH_L if self.type == "clownfish" else BLUETANG_L

        # Draw the sprite onto Pillow canvas
        for row_idx, line in enumerate(sprite):
            for col_idx, char in enumerate(line):
                if char != ' ' and char in COLOR_MAP:
                    draw.point((int(self.x) + col_idx, int(self.y) + row_idx), fill=COLOR_MAP[char])

        # Draw a floating pink heart above the fish if it recently ate
        if time.time() - self.heart_timer < 1.0:
            hx, hy = int(self.x) + 1, int(self.y) - 4
            # Draw a 3x3 heart shape
            # . H .
            # H H H
            # . H .
            draw.point((hx + 1, hy), fill=PINK_HEART)
            draw.point((hx, hy + 1), fill=PINK_HEART)
            draw.point((hx + 1, hy + 1), fill=PINK_HEART)
            draw.point((hx + 2, hy + 1), fill=PINK_HEART)
            draw.point((hx + 1, hy + 2), fill=PINK_HEART)


def run(stop_event):
    logging.info("[Aquarium Mode] Starting Cozy Virtual Aquarium simulation...")

    # Clear old items in the queue
    while not food_queue.empty():
        try:
            food_queue.get_nowait()
        except queue.Empty:
            break

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
            logging.error(f"[Aquarium Mode] Failed to initialize RGBMatrix: {e}")

    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Initialize Marine Life Elements
    # 1. 3 Animated Fishes
    fishes = [
        Fish("clownfish", x=15, y=10, vx=0.2, vy=0.0),
        Fish("blue_tang", x=40, y=16, vx=-0.28, vy=0.0),
        Fish("jellyfish", x=28, y=22, vx=0.0, vy=-0.1)
    ]

    # 2. Seaweed Stalks
    seaweed_bases = [
        {"x": 10, "h": 7, "color": (15, 115, 45)},
        {"x": 20, "h": 10, "color": (25, 130, 55)},
        {"x": 34, "h": 6, "color": (100, 15, 80)},  # Neon magenta seaweed
        {"x": 45, "h": 9, "color": (15, 115, 45)},
        {"x": 56, "h": 8, "color": (25, 130, 55)}
    ]

    # 3. Bubbles
    num_bubbles = 6
    bubbles = []
    for _ in range(num_bubbles):
        bubbles.append({
            "x": random.randint(2, 61),
            "y": random.randint(5, 31),
            "speed": 0.15 + 0.15 * random.random(),
            "wobble": random.uniform(0, 2.0 * math.pi)
        })

    # Active food particles on screen
    active_foods = []

    # Main Loop
    try:
        while not stop_event.is_set():
            t = time.time()

            # ==========================================
            # 1. GENERATE DEEP SEA GRADIENT & GODRAYS
            # ==========================================
            # Deep sea gradient top (0,40,80) to bottom (5,5,25)
            for y in range(height):
                ratio = y / 31.0
                bg_r = int(0 + ratio * 5)
                bg_g = int(40 - ratio * 35)
                bg_b = int(80 - ratio * 55)

                for x in range(width):
                    pixel_r, pixel_g, pixel_b = bg_r, bg_g, bg_b

                    # Godrays shining down at top 16 rows
                    if y < 16:
                        # Moving waves intensity
                        ray_val = math.sin(x * 0.15 + t * 0.8) + math.cos(x * 0.1 - t * 0.4)
                        ray_val = max(0.0, ray_val * (1.0 - y / 16.0))
                        
                        # Add a soft glowing cyan light beam
                        pixel_r = min(255, pixel_r + int(ray_val * 0))
                        pixel_g = min(255, pixel_g + int(ray_val * 16))
                        pixel_b = min(255, pixel_b + int(ray_val * 24))

                    draw.point((x, y), fill=(pixel_r, pixel_g, pixel_b))

            # ==========================================
            # 2. POLL HTTP FOOD QUEUE (DROP FOOD FLAKES)
            # ==========================================
            while not food_queue.empty():
                try:
                    new_food = food_queue.get_nowait()
                    active_foods.append({
                        "x": float(new_food["x"]),
                        "y": 0.0,
                        "id": new_food["id"],
                        "settled_time": 0.0
                    })
                except queue.Empty:
                    break

            # ==========================================
            # 3. UPDATE & DRAW FOOD FLAKES
            # ==========================================
            next_foods = []
            for food in active_foods:
                if food["settled_time"] > 0.0:
                    # Food has settled on bottom. Stays for 3s before decaying
                    if t - food["settled_time"] < 3.0:
                        next_foods.append(food)
                        # Draw settled food particle at the bottom
                        draw.point((int(food["x"]), 31), fill=GOLDEN_FOOD)
                else:
                    # Fluttering downwards motion
                    food["y"] += 0.15 + 0.04 * math.sin(t * 5.0 + food["id"])
                    food["x"] += 0.12 * math.cos(t * 3.0 + food["id"])

                    # Enforce borders
                    if food["x"] < 1:
                        food["x"] = 1
                    elif food["x"] > 62:
                        food["x"] = 62

                    if food["y"] >= 31:
                        food["y"] = 31.0
                        food["settled_time"] = t
                    
                    next_foods.append(food)
                    draw.point((int(food["x"]), int(food["y"])), fill=GOLDEN_FOOD)

            active_foods = next_foods

            # ==========================================
            # 4. UPDATE & DRAW BUBBLE PARTICLES
            # ==========================================
            bubble_color = (130, 210, 255)
            for bubble in bubbles:
                # Floating upwards speed
                bubble["y"] -= bubble["speed"]
                # Horizontal wind/wobble current
                bubble["x"] += 0.25 * math.sin(bubble["y"] * 0.2 + bubble["wobble"])

                # Recycle bubble when it hits the surface
                if bubble["y"] < 0:
                    bubble["y"] = 31
                    bubble["x"] = random.randint(1, 62)
                    bubble["speed"] = 0.15 + 0.15 * random.random()

                # Render bubble pixel
                bx, by = int(bubble["x"]), int(bubble["y"])
                if 0 <= bx < 64 and 0 <= by < 32:
                    draw.point((bx, by), fill=bubble_color)

            # ==========================================
            # 5. UPDATE & DRAW FLORA (SWAYING SEAWEED)
            # ==========================================
            for sw in seaweed_bases:
                base_x = sw["x"]
                h = sw["h"]
                color = sw["color"]

                for y in range(32 - h, 32):
                    # Height relative to base
                    dist_from_base = 31 - y
                    # Tips-only sway: sway displacement scales linearly with height
                    sway = math.sin(t * 1.5 + y * 0.25) * 1.8 * (dist_from_base / float(h))
                    draw_x = int(base_x + sway)
                    if 0 <= draw_x < 64:
                        draw.point((draw_x, y), fill=color)

            # ==========================================
            # 6. UPDATE, DRAW & HUNTING AI FOR FISHES
            # ==========================================
            for fish in fishes:
                fish.update(t, active_foods)
                
                # Check for eating collisions
                if fish.type != "jellyfish" and fish.state == "hunting" and fish.target_food:
                    fx = int(fish.target_food["x"])
                    fy = int(fish.target_food["y"])
                    
                    # Inside fish bounding box coordinates
                    # Fish width is 5, height is 3
                    x_start = int(fish.x)
                    x_end = x_start + fish.width
                    y_start = int(fish.y)
                    y_end = y_start + fish.height
                    
                    if x_start <= fx <= x_end and y_start <= fy <= y_end:
                        # EAT FOOD!
                        if fish.target_food in active_foods:
                            active_foods.remove(fish.target_food)
                        fish.state = "cruising"
                        fish.target_food = None
                        fish.heart_timer = t  # Set floating heart trigger
                
                # Draw the fish
                fish.draw(draw)

            # Frame delay ~30 FPS for fluid water movement and fish speeds
            time.sleep(0.033)

            # Update Display Canvas
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)

    except KeyboardInterrupt:
        logging.info("[Aquarium Mode] Exiting via keyboard interrupt.")
    finally:
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        logging.info("[Aquarium Mode] Stopped Virtual Aquarium clock cleanly.")
