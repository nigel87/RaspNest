import os
import requests
import subprocess
import time
import threading

API_KEY = "bb38d5d6bcebd3b330d05311007a4bd0"
CITY = 'Rome,IT'
ZIP_CODE = "IT"

def stop_clock():
    try:
        subprocess.run(["pkill", "-2", "clock"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed

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
    while not stop_event.is_set():
        temperature = get_weather(CITY, ZIP_CODE)
        display_text = f"{temperature}"

        # Define the command to run the clock binary
        cmd = [
            "sudo", "./clock", "-f", "../fonts/9x18.bdf", display_text,
            "--led-no-hardware-pulse", "--led-cols=64", "--led-gpio-mapping=adafruit-hat", "--led-slowdown-gpio=4", "-s=1", "-y=16"
        ]

        # Change to the directory containing the binary
        current_dir = os.getcwd()
        os.chdir(cpp_binary_folder)

        process = subprocess.Popen(cmd)

        try:
            while not stop_event.is_set():
                time.sleep(1)
        finally:
            process.terminate()
            process.wait()
            os.chdir(current_dir)

        time.sleep(600)  # Fetch weather every 10 minutes

if __name__ == "__main__":
    stop_event = threading.Event()
    cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')
    run(cpp_binary_folder, stop_event)
