import subprocess
import time
import os
import concurrent.futures
import signal
import logging
from python_server.shared.constants import CPP_BINARY_PATH, CPP_BINARY_FOLDER, TEMP_FILE, CPP_CLOCK_WITH_TEXT_PATH

BASE_DISPLAY_TIME = 1.9
SCALE_FACTOR = 0.33

clock_process = None  # Global variable to keep track of the clock subprocess


def run_clock_on_matrix_with_timeout(stop_event, timeout=30):
    global clock_process
    cmd = [
        "sudo", "./clock", "-f", "../fonts/9x18.bdf", TEMP_FILE,
        "--led-no-hardware-pulse", "--led-cols=64", "--led-gpio-mapping=adafruit-hat", "--led-slowdown-gpio=4", "-s=1", "-y=16"
    ]

    current_dir = os.getcwd()
    os.chdir(CPP_BINARY_FOLDER)

    clock_process = subprocess.Popen(cmd)

    start_time = time.time()  # Track the time when the process started

    try:
        # Run clock for 'timeout' seconds or until stop_event is set
        while not stop_event.is_set() and (time.time() - start_time) < timeout:
            time.sleep(1)  # Check every second
    finally:
        if clock_process:
            clock_process.terminate()
            clock_process.wait()
            clock_process = None
        os.chdir(current_dir)


def run_clock_on_matrix(stop_event):
    global clock_process
    cmd = [
        "sudo", "./clock", "-f", "../fonts/9x18.bdf", TEMP_FILE,
        "--led-no-hardware-pulse", "--led-cols=64", "--led-gpio-mapping=adafruit-hat", "--led-slowdown-gpio=4", "-s=1", "-y=16"
    ]

    current_dir = os.getcwd()
    os.chdir(CPP_BINARY_FOLDER)

    clock_process = subprocess.Popen(cmd)

    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        if clock_process:
            clock_process.terminate()
            clock_process.wait()
            clock_process = None
        os.chdir(current_dir)
        

def stop_clock_process():
    global clock_process
    if clock_process:
        try:
            clock_process.terminate()  # Send SIGTERM to terminate gracefully
            clock_process.wait()  # Wait for the process to terminate
        except Exception as e:
            logging.error(f"Error stopping clock process: {e}")
        finally:
            clock_process = None


def preprocess_text(text):
    if not isinstance(text, str):
        return text

    # Read latest configuration to check options
    config = {
        "news_uppercase": False,
        "news_normalize": True
    }
    try:
        import json
        from python_server.shared.constants import WIDGET_CONFIG_FILE
        if os.path.exists(WIDGET_CONFIG_FILE):
            with open(WIDGET_CONFIG_FILE, 'r') as f:
                config.update(json.load(f))
    except Exception as e:
        logging.error(f"Error reading widget config for text preprocess: {e}")

    # 1. Handle language normalization (accented characters like Ç/Ë -> C/E)
    if config.get("news_normalize", True):
        replacements = {
            'ë': 'e', 'Ë': 'E',
            'ç': 'c', 'Ç': 'C',
            'à': 'a', 'À': 'A',
            'è': 'e', 'È': 'E',
            'é': 'e', 'É': 'E',
            'ì': 'i', 'Ì': 'I',
            'ò': 'o', 'Ò': 'O',
            'ù': 'u', 'Ù': 'U',
            'â': 'a', 'Â': 'A',
            'ê': 'e', 'Ê': 'E',
            'î': 'i', 'Î': 'I',
            'ô': 'o', 'Ô': 'O',
            'û': 'u', 'Û': 'U',
            'ä': 'a', 'Ä': 'A',
            'ö': 'o', 'Ö': 'O',
            'ü': 'u', 'Ü': 'U',
            'ñ': 'n', 'Ñ': 'N'
        }
        for k, v in replacements.items():
            text = text.replace(k, v)

    # 2. Handle uppercase conversion
    if config.get("news_uppercase", False):
        text = text.upper()

    return text

def display_on_matrix(title, colour, stop_event):
    if not os.path.exists(CPP_BINARY_PATH):
        logging.error(f"Errore: Il file binario non esiste al percorso: {CPP_BINARY_PATH}")
        return

    if not os.access(CPP_BINARY_PATH, os.X_OK):
        logging.error(f"Errore: Il file binario non ha i permessi di esecuzione: {CPP_BINARY_PATH}")
        return

    # Preprocess text according to settings (normalization and casing)
    title = preprocess_text(title)

    args = [CPP_BINARY_PATH, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'), title,
            '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
            '--led-slowdown-gpio=4',
            '-C', colour]

    start_scrolling_text(args)

    display_time = calculate_display_time(title)
    start_time = time.time()
    
    while time.time() - start_time < display_time:
        if stop_event.is_set():
            stop_scrolling_text()
            return
        time.sleep(0.1)  # Check every 0.1 seconds

    stop_scrolling_text()



def stop_scrolling_text():
    try:
        # Send SIGINT signal as root to cleanly stop the C++ binaries running with sudo
        subprocess.run(["sudo", "pkill", "-2", "-f", "clock_with_scrolling_text"])
        subprocess.run(["sudo", "pkill", "-2", "-f", "text-scroller"])
        subprocess.run(["sudo", "pkill", "-2", "-f", "clock"])
        subprocess.run(["sudo", "pkill", "-2", "-f", "dashboard"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed

def run_clock_with_scrolling_text(scroll_text,text_colour,clock_color, stop_event):
    if not os.path.exists(CPP_CLOCK_WITH_TEXT_PATH):
        logging.error(f"Errore: Il file binario non esiste al percorso: {CPP_CLOCK_WITH_TEXT_PATH}")
        return

    if not os.access(CPP_CLOCK_WITH_TEXT_PATH, os.X_OK):
        logging.error(f"Errore: Il file binario non ha i permessi di esecuzione: {CPP_CLOCK_WITH_TEXT_PATH}")
        return

    # Preprocess text according to settings (normalization and casing)
    scroll_text = preprocess_text(scroll_text)

    cmd = [
        CPP_CLOCK_WITH_TEXT_PATH, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'),
        '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
        '--led-slowdown-gpio=4', '-t', scroll_text,
        '-C', clock_color,
        '-c', text_colour
    ]

    logging.debug(f"Command: {cmd}")  # Debugging print
    process = None
    try:
        stop_scrolling_text()  # Stop any previously running text
        process = subprocess.Popen(cmd)
        logging.info(f"Process started with PID: {process.pid}")

        display_time = calculate_display_time(scroll_text)
        start_time = time.time()
        while time.time() - start_time < display_time:
            if stop_event.is_set():
                return
            time.sleep(0.1)  # Check every 0.1 seconds
    finally:
        if process:
            process.terminate()
            process.wait()
            logging.info("Process terminated.")



def start_scrolling_text(args):
    try:
        stop_scrolling_text()
        subprocess.Popen(args)
    except Exception as e:
        logging.error(f"Error starting scrolling text: {str(e)}")


def calculate_display_time(text):
    text_length = len(text)
    display_time = int(BASE_DISPLAY_TIME + (text_length * SCALE_FACTOR))
    return display_time
""


