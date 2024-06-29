import subprocess
import os
import requests
import threading
import time

API_KEY = "bb38d5d6bcebd3b330d05311007a4bd0"
CITY = 'Rome,IT'

def get_weather(city, zip_code):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{zip_code}",
        "appid": API_KEY,
        "units": "metric"  # Use Celsius for temperature
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        temperature = data["main"]["temp"]
        return f"{temperature}°C"
    else:
        print("Failed to retrieve weather data")
        return "N/A"

def run(cpp_binary_folder, stop_event):
    # Fetch the current weather
    temperature = get_weather("Rome", "IT")

    # Command to run the clock binary with weather information
    command = [
        os.path.join(cpp_binary_folder, "clock"),
        "-f", "../fonts/9x18.bdf",
        temperature,
        "--led-no-hardware-pulse",
        "--led-cols=64",
        "--led-gpio-mapping=adafruit-hat",
        "--led-slowdown-gpio=4",
        "-s=1",
        "-y=16"
    ]

    process = subprocess.Popen(command)

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        process.terminate()
        process.wait()

def stop_clock():
    try:
        subprocess.run(["pkill", "-2", "clock"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed
