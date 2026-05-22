import time
import math
import random
import logging
import threading
from PIL import Image, ImageDraw, ImageFont

# Try importing the rgbmatrix library. Fall back to simulation if not on Raspberry Pi.
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_MATRIX = True
except ImportError:
    HAS_MATRIX = False
    logging.warning("[Retro Mode] rgbmatrix library not found. Running in SIMULATION mode.")

# --- Color Definitions ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PEACH = (255, 200, 150)
BROWN = (100, 50, 0)
DARK_BLUE = (0, 0, 128)

# --- Sprite Maps ---
# Mario Sprites (8x10 px)
MARIO_RUN1 = [
    "  RRRR  ",
    " RRRRRR ",
    " OOBBO  ",
    " OOOO   ",
    "  OOOO  ",
    "  RRR   ",
    " RRRRR  ",
    "  BBB   ",
    "  B B   ",
    "  M M   "
]

MARIO_RUN2 = [
    "  RRRR  ",
    " RRRRRR ",
    " OOBBO  ",
    " OOOO   ",
    "  OOOO  ",
    "  RRR   ",
    " RRRRR  ",
    "  BBB   ",
    " BB BB  ",
    " M   M  "
]

MARIO_JUMP = [
    "  RRRR  ",
    " RRRRRR ",
    " OOBBO  ",
    " OOOO   ",
    "  OOOO  ",
    " RRRRR  ",
    " R R R  ",
    "  BBB   ",
    "  B B   ",
    "  M M   "
]

# Goomba Sprite (8x8 px)
GOOMBA = [
    "  MMMM  ",
    " MMMMMM ",
    "MMOMOMMM",
    "MMMMMMMM",
    " M    M ",
    "MM    MM",
    "MM    MM",
    " M    M "
]

# Ghost Sprite (8x8 px)
GHOST = [
    "  CCCC  ",
    " CCCCCC ",
    "CWCWCWCC",
    "CCCCCCCC",
    "CCCCCCCC",
    "CCCCCCCC",
    "C C C C ",
    " C   C  "
]

GHOST_SCARED = [
    "  BBBB  ",
    " BBBBBB ",
    "BWBWBWBB",
    "BBBBBBBB",
    "BBBBBBBB",
    "BWWWWBBB",
    "B B B B ",
    " B   B  "
]

def draw_sprite(draw, x, y, sprite_lines, color_map):
    """
    Draws a custom pixel-art sprite onto a PIL ImageDraw context.
    """
    for row_idx, line in enumerate(sprite_lines):
        for col_idx, char in enumerate(line):
            if char != ' ' and char in color_map:
                draw.point((x + col_idx, y + row_idx), fill=color_map[char])

def run(stop_event, override_mode=None):
    """
    Runs the Retro Gaming & Audio Visualizer Mode (Mode 12).
    Cycles through Pac-Man, Mario, and Vintage Equalizer every 20 seconds.
    """
    logging.info("[Retro Mode] Starting Retro Pixel Art & Visualizer mode...")

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
            logging.error(f"[Retro Mode] Failed to initialize RGBMatrix: {e}")

    # Set up canvas
    width, height = 64, 32
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Sub-modes: 0 = Pac-Man, 1 = Super Mario, 2 = Audio Visualizer
    current_sub_mode = 0
    if override_mode is not None:
        try:
            current_sub_mode = int(override_mode)
        except ValueError:
            if override_mode == "pacman":
                current_sub_mode = 0
            elif override_mode == "mario":
                current_sub_mode = 1
            elif override_mode == "visualizer":
                current_sub_mode = 2

    last_mode_switch = time.time()
    mode_duration = 20.0  # Duration for each animation in seconds

    # --- Animation State Variables ---
    # Pacman
    pac_x = -10
    pac_dir = 1  # 1 = Right, -1 = Left
    pac_mouth = 0
    pac_frightened = False
    frightened_timer = 0
    dots = [True] * 4  # Dots at positions 15, 30, 45, 60

    # Mario
    mario_x = -10
    mario_y = 21
    mario_frame = 0
    mario_jump_t = -1  # -1 means not jumping
    coin_block_hit = False
    coin_y = 0
    coin_anim = 0
    goomba_x = 70

    # Visualizer
    vis_freqs = [0.0] * 10
    vis_speeds = [0.1 + 0.1 * random.random() for _ in range(10)]
    vis_offsets = [random.random() * 2 * math.pi for _ in range(10)]

    # Dynamic Audio input try-catch
    audio_stream = None
    try:
        import pyaudio
        import numpy as np
        p = pyaudio.PyAudio()
        audio_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=512
        )
        logging.info("[Retro Mode] PyAudio input stream successfully opened!")
    except Exception as e:
        logging.info("[Retro Mode] PyAudio initialization bypassed. Using gorgeous dynamic frequency simulation.")

    try:
        while not stop_event.is_set():
            # Clear canvas
            draw.rectangle((0, 0, width, height), fill=BLACK)

            # Handle automatic sub-mode cycle if not overridden
            if override_mode is None:
                if time.time() - last_mode_switch > mode_duration:
                    current_sub_mode = (current_sub_mode + 1) % 3
                    last_mode_switch = time.time()
                    # Reset animation states on switch
                    pac_x = -10 if pac_dir == 1 else 74
                    mario_x = -10
                    mario_jump_t = -1
                    coin_block_hit = False
                    goomba_x = 70

            # --- RENDER SUB-MODES ---

            if current_sub_mode == 0:
                # ==========================================
                # PAC-MAN CHASE & FRIGHTENED MODE
                # ==========================================
                pac_mouth = (pac_mouth + 1) % 4
                
                # Check frightened timeout
                if pac_frightened:
                    frightened_timer += 1
                    if frightened_timer > 100:  # ~10 seconds
                        pac_frightened = False
                        frightened_timer = 0
                        pac_dir = 1
                
                # Update positions
                if not pac_frightened:
                    pac_x += 1.5 * pac_dir
                    # Eat dots
                    for i, dot_x in enumerate([15, 30, 45, 60]):
                        if dots[i] and pac_x >= dot_x - 3:
                            dots[i] = False
                    
                    # Eat big power pellet at the boundary
                    if pac_x >= 60:
                        pac_frightened = True
                        frightened_timer = 0
                        pac_dir = -1  # Turn back and chase ghosts!
                else:
                    pac_x += 1.2 * pac_dir
                    if pac_x < -20:
                        # Reset chase
                        pac_frightened = False
                        pac_dir = 1
                        pac_x = -20
                        dots = [True] * 4

                # 1. Draw Food Dots / Power Pellets
                for i, dot_x in enumerate([15, 30, 45, 60]):
                    if dots[i]:
                        if i == 3:  # Big Power Pellet flashes
                            if (time.time() * 5) % 2 < 1:
                                draw.ellipse([dot_x - 2, 14, dot_x + 2, 18], fill=ORANGE)
                        else:
                            draw.rectangle([dot_x, 15, dot_x + 1, 16], fill=ORANGE)

                # 2. Draw Pac-Man
                pac_y = 16
                mouth_angle = 0 if pac_mouth < 2 else 45
                if pac_dir == 1:
                    draw.pieslice([pac_x - 5, pac_y - 5, pac_x + 5, pac_y + 5], 
                                  start=mouth_angle, end=360 - mouth_angle, fill=YELLOW)
                else:
                    draw.pieslice([pac_x - 5, pac_y - 5, pac_x + 5, pac_y + 5], 
                                  start=180 + mouth_angle, end=180 - mouth_angle, fill=YELLOW)

                # 3. Draw Ghosts
                blinky_color_map = {'C': RED, 'W': WHITE, 'B': BLUE}
                inky_color_map = {'C': CYAN, 'W': WHITE, 'B': BLUE}
                scared_color_map = {'B': DARK_BLUE, 'W': WHITE}

                if not pac_frightened:
                    # Blinky (Red) chases Pac-man closely
                    draw_sprite(draw, int(pac_x - 14), pac_y - 4, GHOST, blinky_color_map)
                    # Inky (Cyan) follows Blinky
                    draw_sprite(draw, int(pac_x - 26), pac_y - 4, GHOST, inky_color_map)
                else:
                    # Scared blue ghosts run away in front of Pac-Man (who is going left)
                    # Flashes white near the end of timeout
                    color_map = scared_color_map
                    if frightened_timer > 80 and (frightened_timer % 4 < 2):
                        color_map = {'B': WHITE, 'W': RED}
                    
                    draw_sprite(draw, int(pac_x - 22), pac_y - 4, GHOST_SCARED, color_map)
                    draw_sprite(draw, int(pac_x - 36), pac_y - 4, GHOST_SCARED, color_map)

                time.sleep(0.08)

            elif current_sub_mode == 1:
                # ==========================================
                # SUPER MARIO RUN & PIPE VAULT
                # ==========================================
                # Update positions
                mario_x += 1.5
                if mario_x > 75:
                    mario_x = -15
                    coin_block_hit = False
                    goomba_x = 70

                # Goomba moves left
                goomba_x -= 0.8
                if goomba_x < -10:
                    goomba_x = 70

                # 1. Parabolic jumping logic
                # Jump triggered by Coin Block or Goomba
                if mario_jump_t == -1:
                    # Trigger jump over Goomba/Pipe
                    if (mario_x >= 12 and mario_x <= 16 and not coin_block_hit):
                        mario_jump_t = 0
                    elif (mario_x >= 34 and mario_x <= 38):
                        mario_jump_t = 0
                
                if mario_jump_t >= 0:
                    # Parabole: y = ground - amplitude * sin(...)
                    # Jump duration: 16 frames
                    mario_jump_t += 1
                    t_normalized = (mario_jump_t / 16.0) * math.pi
                    mario_y = 21 - int(12 * math.sin(t_normalized))
                    
                    # Coin block interaction
                    if mario_x >= 22 and mario_x <= 28 and mario_jump_t >= 4 and not coin_block_hit:
                        coin_block_hit = True
                        coin_y = 1
                        coin_anim = 8
                    
                    if mario_jump_t >= 16:
                        mario_jump_t = -1
                        mario_y = 21
                else:
                    mario_y = 21

                # 2. Draw ground (y = 31 is solid ground)
                draw.line((0, 31, width, 31), fill=BROWN)
                for gx in range(0, width, 4):
                    draw.point((gx, 31), fill=ORANGE)

                # 3. Draw Green Pipe (x = 48, y = 23 to 30)
                draw.rectangle((48, 23, 58, 30), fill=GREEN, outline=(0, 100, 0))
                draw.line((47, 23, 59, 23), fill=GREEN)
                draw.line((47, 24, 59, 24), fill=GREEN)

                # 4. Draw Coin Block (x = 24, y = 10)
                block_color = ORANGE if not coin_block_hit else BROWN
                draw.rectangle((24, 10, 30, 16), fill=block_color, outline=WHITE if not coin_block_hit else BLACK)
                if not coin_block_hit:
                    # Draw Question Mark '?' inside the block
                    draw.point((27, 11), fill=WHITE)
                    draw.point((26, 12), fill=WHITE)
                    draw.point((28, 12), fill=WHITE)
                    draw.point((27, 13), fill=WHITE)
                    draw.point((27, 15), fill=WHITE)

                # Animate coin popping out
                if coin_block_hit and coin_anim > 0:
                    coin_anim -= 1
                    coin_y += 2
                    cy = 10 - coin_y
                    if coin_anim > 3:
                        draw.ellipse((26, cy - 1, 28, cy + 1), fill=YELLOW)

                # 5. Draw Goomba
                goomba_color_map = {'M': BROWN, 'O': PEACH}
                draw_sprite(draw, int(goomba_x), 24, GOOMBA, goomba_color_map)

                # 6. Draw Mario
                mario_color_map = {'R': RED, 'O': PEACH, 'B': BLUE, 'M': BROWN}
                if mario_jump_t >= 0:
                    draw_sprite(draw, int(mario_x), mario_y, MARIO_JUMP, mario_color_map)
                else:
                    mario_frame = (mario_frame + 1) % 4
                    sprite = MARIO_RUN1 if mario_frame < 2 else MARIO_RUN2
                    draw_sprite(draw, int(mario_x), mario_y, sprite, mario_color_map)

                time.sleep(0.08)

            elif current_sub_mode == 2:
                # ==========================================
                # VINTAGE AUDIO EQUALIZER VISUALIZER
                # ==========================================
                bar_count = 10
                bar_width = 4
                bar_gap = 2
                start_x = 3

                # 1. Fetch Real or Simulated frequencies
                if audio_stream is not None:
                    try:
                        # Non-blocking read
                        data = audio_stream.read(512, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        # Perform fast FFT and downscale to 10 bands
                        fft_vals = np.abs(np.fft.rfft(audio_data))[:bar_count]
                        # Scale factor
                        max_val = np.max(fft_vals) if np.max(fft_vals) > 0 else 1
                        for b in range(bar_count):
                            h = int((fft_vals[b] / max_val) * 28)
                            vis_freqs[b] = max(2, min(28, h))
                    except Exception:
                        # Fallback silently on buffer error
                        pass
                else:
                    # Simulated frequency flow with beautiful noise wave function
                    t = time.time()
                    for b in range(bar_count):
                        # LFO calculation with primary sine waves + small high-frequency random component
                        wave = math.sin(t * 5.0 * vis_speeds[b] + vis_offsets[b])
                        wave_cos = math.cos(t * 2.5 * vis_speeds[b] - vis_offsets[b])
                        # Normalize wave between 0.0 and 1.0
                        amp = (wave + wave_cos + 2.0) / 4.0
                        # Map to height 2 to 28
                        h = int(2 + amp * 23 + random.randint(-2, 2))
                        vis_freqs[b] = max(2, min(28, h))

                # 2. Draw the vertical gradient bars
                for b in range(bar_count):
                    bar_h = int(vis_freqs[b])
                    bx = start_x + b * (bar_width + bar_gap)
                    by = 30 - bar_h

                    # Draw bar color-segmented pixel-by-pixel (gradient)
                    for py in range(by, 31):
                        if py >= 24:
                            color = GREEN  # Safe
                        elif py >= 12:
                            color = YELLOW  # Warning
                        else:
                            color = RED  # Peak / Clip
                        
                        # Draw a horizontal line of width 4 for the bar segment
                        draw.line((bx, py, bx + bar_width - 1, py), fill=color)

                time.sleep(0.04)  # Faster framerate for high-fidelity equalizer bars

            # --- UPDATE DISPLAY CANVAS ---
            if HAS_MATRIX and matrix is not None:
                matrix.SetImage(image)
            else:
                # Keep CPU usage clean if running local simulations
                pass

    except KeyboardInterrupt:
        logging.info("[Retro Mode] Exiting via manual interrupt.")
    finally:
        # Clean shutdown and clear matrix
        if HAS_MATRIX and matrix is not None:
            matrix.Clear()
            del matrix
            import gc
            gc.collect()
        if audio_stream is not None:
            try:
                audio_stream.stop_stream()
                audio_stream.close()
            except Exception:
                pass
        logging.info("[Retro Mode] Stopped Retro Pixel Art & Visualizer display cleanly.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stop_event = threading.Event()
    # Test Pac-Man mode locally
    try:
        run(stop_event, override_mode=0)
    except KeyboardInterrupt:
        stop_event.set()
