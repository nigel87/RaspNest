import subprocess
import time
import os
from python_server.constants import CPP_BINARY_PATH, CPP_BINARY_FOLDER

BASE_DISPLAY_TIME = 1.9
SCALE_FACTOR = 0.135

def calculate_display_time(text):
    text_length = len(text)
    display_time = int(BASE_DISPLAY_TIME + (text_length * SCALE_FACTOR))
    return display_time


def display_on_matrix(title, colour):
    if not os.path.exists(CPP_BINARY_PATH):
        print(f"Errore: Il file binario non esiste al percorso: {CPP_BINARY_PATH}")
        return

    if not os.access(CPP_BINARY_PATH, os.X_OK):
        print(f"Errore: Il file binario non ha i permessi di esecuzione: {CPP_BINARY_PATH}")
        return

    args = [CPP_BINARY_PATH, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'), title,
          '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
          '--led-slowdown-gpio=4',
          '-C', colour]
    start_scrolling_text(args)
    time.sleep(calculate_display_time(title))

def stop_scrolling_text():
    try:
        # Send SIGINT signal to stop the scrolling text
        subprocess.run(["pkill", "-2", "text-scroller"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed


def start_scrolling_text(args):
    try:
        stop_scrolling_text()
        subprocess.Popen(args)
    except Exception as e:
        print(f"Error starting scrolling text: {str(e)}")
