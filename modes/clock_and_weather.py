import os
import requests
import subprocess
import time
import threading

from python_server.constants import *
from python_server.scrolling_text_controller import run_clock_on_matrix
from python_server.shared.weather_service import get_weather_rome


def run(stop_event):
    # Create and start the thread to update temperature
    temperature_thread = threading.Thread(target=update_temperature_periodically, args=(stop_event,))
    temperature_thread.start()

    try:
        run_clock_on_matrix(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
        temperature_thread.join()
        stop_clock()


def stop_clock():
    try:
        subprocess.run(["pkill", "-2", "clock"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed



def write_temperature_to_file(temperature):
    with open(TEMP_FILE, "w") as file:
        file.write(temperature)



def update_temperature_periodically(stop_event):
    while not stop_event.is_set():
        temperature = str(get_weather_rome()["main"]["temp"])
        write_temperature_to_file(temperature)
        for _ in range(600):  # Check stop_event every second for 10 minutes
            if stop_event.is_set():
                break
            time.sleep(1)



if __name__ == "__main__":
    stop_event = threading.Event()
    CPP_BINARY_FOLDER = os.path.join(os.path.dirname(__file__), '../c')
    run(stop_event)