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

# --- Thread-Safe Queue for Interactive Sand Drops ---
# External components can call sand_queue.put({"x": x, "color": (r, g, b)})
sand_queue = queue.Queue()

# --- Color Palettes ---
BLACK = (0, 0, 0)
NEON_PINK = (255, 0, 150)
NEON_CYAN = (0, 240, 255)
NEON_YELLOW = (255, 230, 0)
NEON_GREEN = (0, 255, 80)
NEON_ORANGE = (255, 100, 0)

AUTO_SPOUT_COLORS = [NEON_PINK, NEON_CYAN, NEON_YELLOW]
AUTO_SPOUT_COLS = [16, 32, 48]

def run(stop_event):
    logging.info("[Sand Physics] Starting Sand Physics & Interactive Fluid Art...")

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

    # Vortex dissolve frame tracker for animation
    vortex_active = False
    vortex_frame = 0

    try:
        while not stop_event.is_set():
            if vortex_active:
                # ==========================================
                # DISSOLVE / CLEAR ANIMATION
                # ==========================================
                vortex_frame += 1
                
                # Dynamic circle dissolve (expanding black hole from center)
                cx, cy = 32, 16
                r = int(vortex_frame * 3.5)
                
                draw.rectangle((0, 0, width - 1, height - 1), fill=BLACK)
                # Redraw grid but clip inside the expanding black circle
                for gy in range(height):
                    for gx in range(width):
                        if grid[gy][gx] is not None:
                            dist = math.sqrt((gx - cx)**2 + (gy - cy)**2) if 'math' in globals() else abs(gx - cx) + abs(gy - cy)
                            if dist > r:
                                draw.point((gx, gy), fill=grid[gy][gx])
                
                if r > 50: # Reset canvas after full dissolve
                    grid = [[None for _ in range(width)] for _ in range(height)]
                    vortex_active = False
                    vortex_frame = 0
                    
                time.sleep(0.04)
            else:
                # ==========================================
                # PHYSICS CELLULAR AUTOMATON STEP
                # ==========================================
                # 1. Spawn automatic sand from spouts
                for i, col in enumerate(AUTO_SPOUT_COLS):
                    if random.random() < 0.25: # 25% chance per spout per frame
                        color = AUTO_SPOUT_COLORS[i]
                        # Spawn at the very top (y=0) if empty
                        if grid[0][col] is None:
                            grid[0][col] = color

                # 2. Consume sand from the interactive REST API queue
                while not sand_queue.empty():
                    try:
                        drop_data = sand_queue.get_nowait()
                        rx = max(0, min(width - 1, int(drop_data.get("x", 32))))
                        # Read custom color or assign a random vibrant one
                        raw_color = drop_data.get("color")
                        if isinstance(raw_color, tuple) and len(raw_color) == 3:
                            r_col = raw_color
                        else:
                            r_col = random.choice([NEON_GREEN, NEON_ORANGE, WHITE])
                        
                        # Spawn at top if column is free
                        if grid[0][rx] is None:
                            grid[0][rx] = r_col
                    except queue.Empty:
                        break

                # 3. Apply sand physics logic
                # Iterate from bottom to top (y=30 down to 0) to avoid moving the same pixel twice
                for gy in range(height - 2, -1, -1):
                    for gx in range(width):
                        pixel_color = grid[gy][gx]
                        if pixel_color is None:
                            continue

                        # Check slot directly below
                        if grid[gy + 1][gx] is None:
                            grid[gy + 1][gx] = pixel_color
                            grid[gy][gx] = None
                        else:
                            # Slide down left or right
                            left_free = (gx - 1 >= 0) and (grid[gy + 1][gx - 1] is None)
                            right_free = (gx + 1 < width) and (grid[gy + 1][gx + 1] is None)

                            if left_free and right_free:
                                # Both free, choose randomly
                                dx = random.choice([-1, 1])
                                grid[gy + 1][gx + dx] = pixel_color
                                grid[gy][gx] = None
                            elif left_free:
                                grid[gy + 1][gx - 1] = pixel_color
                                grid[gy][gx] = None
                            elif right_free:
                                grid[gy + 1][gx + 1] = pixel_color
                                grid[gy][gx] = None

                # 4. Check if sand pile has hit the top limit (column columns peak at y <= 4)
                # We check multiple contiguous cells (y=4, 5, 6, 7) to ensure it's a solid accumulated
                # pile/pyramid peak, and not just a single falling sand grain passing through.
                pile_limit_reached = False
                for col in AUTO_SPOUT_COLS:
                    if (grid[4][col] is not None and 
                        grid[5][col] is not None and 
                        grid[6][col] is not None and 
                        grid[7][col] is not None):
                        pile_limit_reached = True
                        break

                if pile_limit_reached:
                    # Trigger the dynamic dissolve transition
                    vortex_active = True
                    vortex_frame = 0

                # 5. Draw active pixels to Pillow canvas
                draw.rectangle((0, 0, width - 1, height - 1), fill=BLACK)
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
        logging.info("[Sand Physics] Stopped Sand Physics screensaver cleanly.")

if __name__ == "__main__":
    import threading
    logging.basicConfig(level=logging.INFO)
    stop_event = threading.Event()
    try:
        run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
