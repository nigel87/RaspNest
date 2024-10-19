import subprocess
import time
import os
import concurrent.futures
import signal
from python_server.shared.constants import CPP_BINARY_PATH, CPP_BINARY_FOLDER, TEMP_FILE, CPP_CLOCK_WITH_TEXT_PATH

BASE_DISPLAY_TIME = 1.9
SCALE_FACTOR = 0.135

clock_process = None  # Global variable to keep track of the clock subprocess


def run_clock_on_matrix(stop_event):
    global clock_process
    cmd = [
        "sudo", "./clock", "-f", "../fonts/9x18.bdf", TEMP_FILE,
        "--led-no-hardware-pulse", "--led-cols=64", "--led-gpio-mapping=adafruit-hat", "--led-slowdown-gpio=4", "-s=1", "-y=16"
    ]

    current_dir = os.getcwd()
    os.chdir(CPP_BINARY_FOLDER)

    process = subprocess.Popen(cmd)

    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        process.terminate()
        process.wait()
        os.chdir(current_dir)
        

def stop_clock_process():
    global clock_process
    if clock_process:
        try:
            clock_process.terminate()  # Send SIGTERM to terminate gracefully
            clock_process.wait()  # Wait for the process to terminate
        except Exception as e:
            print(f"Error stopping clock process: {e}")
        finally:
            clock_process = None


def display_on_matrix(title, colour, stop_event):
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
        # Send SIGINT signal to stop the scrolling text or clock with scrolling text
        # Use pkill -f to match the full command line for processes with long names
        subprocess.run(["pkill", "-2", "-f", "clock_with_scrolling_text"])
        subprocess.run(["pkill", "-2", "-f", "text-scroller"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed

def run_clock_with_scrolling_text(scroll_text,text_colour,clock_color, stop_event):
    if not os.path.exists(CPP_CLOCK_WITH_TEXT_PATH):
        print(f"Errore: Il file binario non esiste al percorso: {CPP_CLOCK_WITH_TEXT_PATH}")
        return

    if not os.access(CPP_CLOCK_WITH_TEXT_PATH, os.X_OK):
        print(f"Errore: Il file binario non ha i permessi di esecuzione: {CPP_CLOCK_WITH_TEXT_PATH}")
        return


    cmd = [
        CPP_CLOCK_WITH_TEXT_PATH, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'),
        '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
        '--led-slowdown-gpio=4', '-t', scroll_text,
        '-C', clock_color,
        '-c', text_colour
    ]

    print(f"Command: {cmd}")  # Debugging print

    try:
        stop_scrolling_text()  # Stop any previously running text
        process = subprocess.Popen(cmd)
        print(f"Process started with PID: {process.pid}")
    except Exception as e:
        print(f"Error starting process: {str(e)}")
        return

    try:
        display_time = calculate_display_time(scroll_text)
        start_time = time.time()
        while time.time() - start_time < display_time:
            if stop_event.is_set():
                stop_scrolling_text()
                return
        time.sleep(0.1)  # Check every 0.1 seconds

    finally:
        process.terminate()
        process.wait()
        print("Process terminated.")


def start_scrolling_text(args):
    try:
        stop_scrolling_text()
        subprocess.Popen(args)
    except Exception as e:
        print(f"Error starting scrolling text: {str(e)}")


def calculate_display_time(text):
    text_length = len(text)
    display_time = int(BASE_DISPLAY_TIME + (text_length * SCALE_FACTOR))
    return display_time


