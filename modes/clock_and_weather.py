import os
import requests
import subprocess
import time
import threading

from python_server.constants import *
from python_server.shared.weather_service import get_weather_rome




def stop_clock():
    try:
        subprocess.run(["pkill", "-2", "clock"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed



def write_temperature_to_file(temperature):
    with open(TEMP_FILE, "w") as file:
        file.write(temperature)

def run_clock(stop_event):
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

def update_temperature_periodically(stop_event):
    while not stop_event.is_set():
        temperature = str(get_weather_rome()["main"]["temp"])
        write_temperature_to_file(temperature)
        for _ in range(600):  # Check stop_event every second for 10 minutes
            if stop_event.is_set():
                break
            time.sleep(1)

def run(stop_event):
    # Create and start the thread to update temperature
    temperature_thread = threading.Thread(target=update_temperature_periodically, args=(stop_event,))
    temperature_thread.start()

    try:
        run_clock(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
        temperature_thread.join()
        stop_clock()

if __name__ == "__main__":
    stop_event = threading.Event()
    CPP_BINARY_FOLDER = os.path.join(os.path.dirname(__file__), '../c')
    run(stop_event)