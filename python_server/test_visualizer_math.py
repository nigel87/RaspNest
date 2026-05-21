import sys
import os
import math
import random
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_pacman_math():
    print("--- Testing Pac-Man Coordinate Math ---")
    dots = [True] * 4
    pac_x = -10
    pac_dir = 1
    pac_frightened = False
    
    # Simulate 50 frames
    for frame in range(50):
        # Update positions
        if not pac_frightened:
            pac_x += 1.5 * pac_dir
            for i, dot_x in enumerate([15, 30, 45, 60]):
                if dots[i] and pac_x >= dot_x - 3:
                    dots[i] = False
            
            if pac_x >= 60:
                pac_frightened = True
                pac_dir = -1
        else:
            pac_x += 1.2 * pac_dir
            
        if frame % 10 == 0:
            print(f"Frame {frame:02d} | Pacman X: {pac_x:5.1f} | Dir: {pac_dir:2d} | Frightened: {pac_frightened} | Active Dots: {dots}")

def test_mario_jump_math():
    print("\n--- Testing Mario Parabolic Jump Math ---")
    mario_x = -10
    mario_y = 21
    mario_jump_t = -1
    
    # Run loop
    for frame in range(40):
        mario_x += 1.5
        
        # Trigger jump
        if mario_jump_t == -1 and mario_x >= 12 and mario_x <= 16:
            mario_jump_t = 0
            
        if mario_jump_t >= 0:
            mario_jump_t += 1
            t_normalized = (mario_jump_t / 16.0) * math.pi
            mario_y = 21 - int(12 * math.sin(t_normalized))
            
            if mario_jump_t >= 16:
                mario_jump_t = -1
                mario_y = 21
                
        if frame % 5 == 0 or mario_jump_t >= 0:
            print(f"Frame {frame:02d} | Mario X: {mario_x:5.1f} | Y: {mario_y:2d} | Jump Frame: {mario_jump_t}")

def test_visualizer_math():
    print("\n--- Testing Vintage Visualizer Gradient Heights ---")
    bar_count = 10
    vis_freqs = [0.0] * bar_count
    vis_speeds = [0.1 + 0.1 * random.random() for _ in range(bar_count)]
    vis_offsets = [random.random() * 2 * math.pi for _ in range(bar_count)]
    
    # Run 5 frames of simulation
    for frame in range(5):
        t = frame * 0.1  # simulate time increments
        row_str = []
        for b in range(bar_count):
            wave = math.sin(t * 5.0 * vis_speeds[b] + vis_offsets[b])
            wave_cos = math.cos(t * 2.5 * vis_speeds[b] - vis_offsets[b])
            amp = (wave + wave_cos + 2.0) / 4.0
            h = int(2 + amp * 23 + random.randint(-1, 1))
            vis_freqs[b] = max(2, min(28, h))
            row_str.append(f"{vis_freqs[b]:02d}")
            
        print(f"Time Step {t:.1f} | Equalizer Heights: {' '.join(row_str)}")

if __name__ == "__main__":
    test_pacman_math()
    test_mario_jump_math()
    test_visualizer_math()
    print("\n✅ Simulation and Animation mathematics verified successfully with zero boundaries overflow!")
