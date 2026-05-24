import os
import time
import subprocess
import logging
from python_server.shared.constants import CPP_BINARY_FOLDER
from python_server.shared.controller.matrix_controller import run_clock_on_matrix_with_timeout, stop_scrolling_text

def run(stop_event):
    """
    Runs the Cozy Minimalist Dashboard (Mode 17).
    Alternates between:
      1. Displaying the beautiful retro pixel-art Cozy Fireplace GIF for 12 seconds.
      2. Displaying the elegant Full-Screen Clock and Weather for 12 seconds.
    """
    logging.info("[Main Cozy] Starting Cozy Minimalist Dashboard...")
    stop_scrolling_text()

    cpp_image_viewer = os.path.join(CPP_BINARY_FOLDER, 'led-image-viewer')
    fireplace_path = "../assets/gif/Fireplace.gif"

    while not stop_event.is_set():
        # --- PHASE 1: Render Cozy Fireplace GIF ---
        if stop_event.is_set():
            break
            
        logging.info("[Main Cozy] Phase 1: Displaying Cozy Fireplace GIF...")
        if os.path.exists(fireplace_path):
            cmd = [
                "sudo", cpp_image_viewer,
                "-w", "12",  # Display/Wait for 12 seconds in C++ binary
                fireplace_path,
                "--led-no-hardware-pulse",
                "--led-cols=58",
                "--led-rows=32",
                "--led-gpio-mapping=adafruit-hat",
                "--led-slowdown-gpio=4"
            ]
            
            process = None
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Check for stop event every 0.1 seconds for 12 seconds
                start_time = time.time()
                while time.time() - start_time < 12.0:
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                logging.error(f"[Main Cozy] Error running image viewer: {e}")
            finally:
                if process:
                    if process.poll() is None:
                        process.terminate()
                        process.wait()
                    logging.info("[Main Cozy] Fireplace display process ended.")
        else:
            logging.warning(f"[Main Cozy] Fireplace GIF not found at {fireplace_path}. Skipping.")
            time.sleep(2)

        # --- PHASE 2: Display Elegant Clock & Weather ---
        if stop_event.is_set():
            break
            
        logging.info("[Main Cozy] Phase 2: Displaying Clock and Weather...")
        try:
            # Displays the full screen clock with weather for 12 seconds
            run_clock_on_matrix_with_timeout(stop_event, timeout=12)
        except Exception as e:
            logging.error(f"[Main Cozy] Error displaying clock: {e}")
            time.sleep(1)

    logging.info("[Main Cozy] Stopped Cozy Minimalist Dashboard.")
