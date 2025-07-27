import subprocess
import threading
import os
import logging
from python_server.shared.controller.matrix_controller import stop_scrolling_text
from python_server.shared.constants import CPP_BINARY_FOLDER

def run(image_path, stop_event):
    stop_scrolling_text()
    logging.info(f"Displaying image: {image_path}")

    cpp_binary = os.path.join(CPP_BINARY_FOLDER, 'led-image-viewer')
    args = [
        "sudo", cpp_binary, "-w", "10", image_path,
        "--led-no-hardware-pulse", "--led-cols=58", "--led-rows=32",
        "--led-gpio-mapping=adafruit-hat", "--led-slowdown-gpio=4"
    ]

    process = None
    try:
        logging.info(f"Calling C++ Image Viewer: {' '.join(args)}")
        process = subprocess.Popen(args)
        logging.info(f"Image viewer process started with PID: {process.pid}")

        while not stop_event.is_set():
            if process.poll() is not None: # Check if process has terminated
                logging.warning("Image viewer process terminated unexpectedly.")
                break
            threading.Event().wait(0.1) # Small delay to prevent busy-waiting

    except Exception as e:
        logging.error(f"Error displaying image: {str(e)}")
    finally:
        if process and process.poll() is None: # If process is still running, terminate it
            process.terminate()
            process.wait()
            logging.info("Image viewer process terminated.")
        logging.info("Image display mode finished.")
