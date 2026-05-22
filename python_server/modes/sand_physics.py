import time
import random
import logging
import queue
import math
from PIL import Image, ImageDraw

# Try importing the rgbmatrix library. Fall back to simulation if not on Raspberry Pi.
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logging.warning("[Sand Physics] rgbmatrix library not found. Running in SIMULATION mode.")

# --- Thread-Safe Queue for Compatibility ---
# Kept for compatibility with server.py and other modules, but drained silently
# to ensure absolutely zero sand is drawn outside the clessidre.
sand_queue = queue.Queue()

# --- Color Palettes ---
BLACK = (0, 0, 0)
NEON_PINK = (255, 0, 150)
NEON_CYAN = (0, 240, 255)
NEON_YELLOW = (255, 230, 0)

# --- Strict Internal Coordinates for the Top Bulb ---
# Maps row 'y' to the exact internal 'dx' offsets (0 to 14) that reside INSIDE the glass walls.
# This prevents spawning any sand on the exterior space.
HG_INTERNAL_TOP_DX = {
    3: range(1, 14),   # dx 1 to 13
    4: range(2, 13),   # dx 2 to 12
    5: range(2, 13),   # dx 2 to 12
    6: range(3, 12),   # dx 3 to 11
    7: range(3, 12),   # dx 3 to 11
    8: range(4, 11),   # dx 4 to 10
    9: range(4, 11),   # dx 4 to 10
    10: range(5, 10),  # dx 5 to 9
    11: range(5, 10),  # dx 5 to 9
    12: range(6, 9),   # dx 6 to 8 (neck approach)
    13: range(6, 9),   # dx 6 to 8
    14: range(6, 9)    # dx 6 to 8
}

def run(stop_event):
    logging.info("[Sand Physics] Starting Pure Hourglass Sand Simulation...")

    # Clear any old items in the queue
    while not sand_queue.empty():
        try:
            sand_queue.get_nowait()
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
            logging.error(f"[Sand Physics] Failed to initialize RGBMatrix: {e}")

    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # 2D Grid tracking color values (y, x coordinates)
    grid = [[None for _ in range(width)] for _ in range(height)]

    # Glass walls mapping (completely sealed at the bottom row 29)
    is_wall = [[False for _ in range(width)] for _ in range(height)]
    
    def build_hourglass(x_offset):
        # Lids (solid and watertight barriers)
        for dx in range(15):
            is_wall[2][x_offset + dx] = True
            is_wall[29][x_offset + dx] = True
        
        # Slanted and neck walls
        # The neck hole is at y=15, x=x_offset+7. We make it a wall physically
        # to block top sand, but we don't draw it as glass to make it look open!
        wall_specs = [
            (2, [0, 14]), (3, [0, 14]), (4, [1, 13]), (5, [1, 13]),
            (6, [2, 12]), (7, [2, 12]), (8, [3, 11]), (9, [3, 11]),
            (10, [4, 10]), (11, [4, 10]), (12, [5, 9]), (13, [5, 9]), (14, [5, 9]),
            (15, [6, 7, 8]), (16, [6, 8]),  # Note: dx=7 is a physical barrier in y=15 to support top bulb particles
            (17, [5, 9]), (18, [5, 9]), (19, [5, 9]), (20, [4, 10]), (21, [4, 10]),
            (22, [3, 11]), (23, [3, 11]), (24, [2, 12]), (25, [2, 12]),
            (26, [1, 13]), (27, [1, 13]), (28, [0, 14]), (29, [0, 14])
        ]
        for y, dxs in wall_specs:
            for dx in dxs:
                is_wall[y][x_offset + dx] = True

    build_hourglass(3)  # Left Hourglass (Pink)
    build_hourglass(24) # Center Hourglass (Cyan)
    build_hourglass(45) # Right Hourglass (Yellow)

    # Define Hourglass data structures
    hg_left = {
        "name": "left",
        "x_offset": 3,
        "color": NEON_PINK,
        "total": 60,
        "last_drop_time": 0.0,
        "drop_interval": 0.8
    }
    
    hg_center = {
        "name": "center",
        "x_offset": 24,
        "color": NEON_CYAN,
        "total": 60,
        "last_drop_time": 0.0,
        "drop_interval": 0.8
    }
    
    hg_right = {
        "name": "right",
        "x_offset": 45,
        "color": NEON_YELLOW,
        "total": 60,
        "last_drop_time": 0.0,
        "drop_interval": 0.8
    }
    
    hourglasses = [hg_left, hg_center, hg_right]

    def populate_hourglass_top(hg):
        x_off = hg["x_offset"]
        color = hg["color"]
        
        # 1. Clear any sand currently inside and immediately outside this hourglass area
        for y in range(32):
            for x in range(x_off, x_off + 15):
                grid[y][x] = None
                     
        # 2. Gather top bulb open coordinates using the strict internal dx mapping
        top_coords = []
        for y in sorted(HG_INTERNAL_TOP_DX.keys(), reverse=True):
            for dx in HG_INTERNAL_TOP_DX[y]:
                top_coords.append((x_off + dx, y))
         
        # 3. Fill top bulb with all total grains
        for i in range(min(hg["total"], len(top_coords))):
            gx, gy = top_coords[i]
            grid[gy][gx] = color

    def drop_grain(hg):
        x_off = hg["x_offset"]
        color = hg["color"]
        
        # Find all sand pixels in the top bulb using the strict internal mapping
        top_pixels = []
        for y in HG_INTERNAL_TOP_DX.keys():
            for dx in HG_INTERNAL_TOP_DX[y]:
                if grid[y][x_off + dx] == color:
                    top_pixels.append((x_off + dx, y))
                    
        if top_pixels:
            # Settle top bulb neatly: pick a pixel from the highest occupied row
            min_y = min(p[1] for p in top_pixels)
            highest_row_pixels = [p for p in top_pixels if p[1] == min_y]
            
            # Remove one grain from the top
            rx, ry = random.choice(highest_row_pixels)
            grid[ry][rx] = None
            
            # Spawn just below the neck hole at y=16
            spawn_x = x_off + 7
            spawn_y = 16
            if grid[spawn_y][spawn_x] is None:
                grid[spawn_y][spawn_x] = color
            else:
                # If occupied, find a free spot nearby
                for sy in [17, 18]:
                    if grid[sy][spawn_x] is None and (not is_wall[sy][spawn_x]):
                        grid[sy][spawn_x] = color
                        break

    def count_top_sand(hg):
        x_off = hg["x_offset"]
        color = hg["color"]
        count = 0
        for y in HG_INTERNAL_TOP_DX.keys():
            for dx in HG_INTERNAL_TOP_DX[y]:
                if grid[y][x_off + dx] == color:
                    count += 1
        return count

    def count_neck_sand(hg):
        x_off = hg["x_offset"]
        color = hg["color"]
        count = 0
        for y in [15, 16, 17]:
            for x in range(x_off, x_off + 15):
                if grid[y][x] == color:
                    count += 1
        return count

    # Initialize all three hourglasses with full sand in their top bulbs
    now = time.time()
    for hg in hourglasses:
        populate_hourglass_top(hg)
        hg["last_drop_time"] = now
        hg["drop_interval"] = random.uniform(0.6, 1.0)

    try:
        while not stop_event.is_set():
            # ==========================================
            # SILENT QUEUE DRAIN (Zero Outside Sand)
            # ==========================================
            while not sand_queue.empty():
                try:
                    sand_queue.get_nowait()
                except queue.Empty:
                    break

            # ==========================================
            # INDEPENDENT TIME-REGULATED DROP & RESET
            # ==========================================
            curr_time = time.time()
            for hg in hourglasses:
                top_count = count_top_sand(hg)
                
                # If top bulb is completely empty and no grains are lingering in the neck, reset it!
                if top_count == 0 and count_neck_sand(hg) == 0:
                    populate_hourglass_top(hg)
                    hg["last_drop_time"] = curr_time
                    hg["drop_interval"] = random.uniform(0.6, 1.0)
                elif top_count > 0:
                    # Drop exactly ONE grain when the customized interval has elapsed
                    if curr_time - hg["last_drop_time"] >= hg["drop_interval"]:
                        drop_grain(hg)
                        hg["last_drop_time"] = curr_time
                        # Re-roll interval for natural, realistic fluid trickling
                        hg["drop_interval"] = random.uniform(0.6, 1.0)

            # ==========================================
            # PHYSICS CELLULAR AUTOMATON STEP
            # ==========================================
            # Apply standard gravity sand physics ONLY to the neck and bottom bulb (gy >= 15).
            # Grains in the top bulb (gy <= 14) stay perfectly still, emptying cleanly from the top.
            for gy in range(height - 2, 14, -1):
                for gx in range(width):
                    pixel_color = grid[gy][gx]
                    if pixel_color is None:
                        continue

                    below_empty = (grid[gy + 1][gx] is None) and (not is_wall[gy + 1][gx])

                    if below_empty:
                        grid[gy + 1][gx] = pixel_color
                        grid[gy][gx] = None
                    else:
                        # Slide down left or right
                        left_free = (gx - 1 >= 0) and (grid[gy + 1][gx - 1] is None) and (not is_wall[gy + 1][gx - 1])
                        right_free = (gx + 1 < width) and (grid[gy + 1][gx + 1] is None) and (not is_wall[gy + 1][gx + 1])

                        if left_free and right_free:
                            dx = random.choice([-1, 1])
                            grid[gy + 1][gx + dx] = pixel_color
                            grid[gy][gx] = None
                        elif left_free:
                            grid[gy + 1][gx - 1] = pixel_color
                            grid[gy][gx] = None
                        elif right_free:
                            grid[gy + 1][gx + 1] = pixel_color
                            grid[gy][gx] = None

            # ==========================================
            # RENDERING PILLOW CANVAS
            # ==========================================
            draw.rectangle((0, 0, width - 1, height - 1), fill=BLACK)
            
            # Draw glass walls for all 3 hourglasses
            wall_color = (60, 80, 110)
            for gy in range(height):
                for gx in range(width):
                    if is_wall[gy][gx]:
                        # Hide the neck support barrier at y=15 so the neck looks open
                        is_hidden_neck = False
                        for hg in hourglasses:
                            if gy == 15 and gx == hg["x_offset"] + 7:
                                is_hidden_neck = True
                                break
                        if not is_hidden_neck:
                            draw.point((gx, gy), fill=wall_color)

            # Draw all sand pixels inside the hourglasses
            for gy in range(height):
                for gx in range(width):
                    if grid[gy][gx] is not None:
                        draw.point((gx, gy), fill=grid[gy][gx])

            # Framerate ~30 FPS for fluid simulation physics
            time.sleep(0.033)

            # Update Display Canvas
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)

    except KeyboardInterrupt:
        logging.info("[Sand Physics] Exiting via keyboard interrupt.")
    finally:
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        logging.info("[Sand Physics] Stopped Sand Physics clock cleanly.")
