import os
import requests
import subprocess
import time
import threading
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text

API_KEY = "bb38d5d6bcebd3b330d05311007a4bd0"
CITY = 'Rome,IT'
ZIP_CODE = "IT"
TEMP_FILE = "/tmp/current_temperature.txt"
CPP_BINARY_FOLDER = os.path.join(os.path.dirname(__file__), '../c')
CPP_BINARY_PATH = os.path.join(CPP_BINARY_FOLDER, 'text-scroller')

BASE_DISPLAY_TIME = 2
SCALE_FACTOR = 0.135

# Define the dictionary mapping color names to their RGB values
colors = {
    "red": "255,0,0",
    "green": "0,255,0",
    "blue": "0,0,255",
    "white": "255,255,255",
    "black": "0,0,0",
    "yellow": "255,255,0",
    "cyan": "0,255,255",
    "magenta": "255,0,255",
    "orange": "255,165,0",
    "purple": "128,0,128",
    "pink": "255,192,203",
    "brown": "165,42,42",
    "grey": "128,128,128",
    "lime": "0,255,0",
    "navy": "0,0,128",
    "gold": "255,215,0"
}

# Assigning all colors as constants
RED = colors["red"]
GREEN = colors["green"]
BLUE = colors["blue"]
WHITE = colors["white"]
BLACK = colors["black"]
YELLOW = colors["yellow"]
CYAN = colors["cyan"]
MAGENTA = colors["magenta"]
ORANGE = colors["orange"]
PURPLE = colors["purple"]
PINK = colors["pink"]
BROWN = colors["brown"]
GREY = colors["grey"]
LIME = colors["lime"]
NAVY = colors["navy"]
GOLD = colors["gold"]

# Function to get the RGB string for a given color name
def get_rgb(color_name):
    return colors.get(color_name.lower(), "Unknown color")

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
        return data
    else:
        print("Failed to retrieve weather data")
        return "N/A"

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

def run(stop_event):
    stop_scrolling_text()
    weather = get_weather(CITY, ZIP_CODE)
    if weather == "N/A":
        return

    temperature = weather["main"]["temp"]
    feels_like = weather["main"]["feels_like"]
    temp_min = weather["main"]["temp_min"]
    temp_max = weather["main"]["temp_max"]
    humidity = weather["main"]["humidity"]
    rain1h = 'NO DATA' #weather ["rain"]["rain.1h"]
    rain3h = 'NO DATA' #weather ["rain"]["rain.3h"]

    displayTitle = 'Temperature: ' + str(temperature) 
    display_on_matrix(displayTitle, GREEN)

    displayTitle = 'Temperatura percepita: ' + str(feels_like) 
    display_on_matrix(displayTitle, YELLOW)

    displayTitle = 'Temperature MIN ' + str(temp_min) 
    display_on_matrix(displayTitle, GREEN)

    displayTitle = 'Temperature MAX ' + str(temp_max) 
    display_on_matrix(displayTitle, RED)

    displayTitle = 'Umidità ' + str(humidity) 
    display_on_matrix(displayTitle, ORANGE)

    #displayTitle = 'Rain in 1h' + str(rain1h) 
    #display_on_matrix(displayTitle, BLUE)

    #displayTitle = 'Rain in 3h' + str(rain3h) 
    #display_on_matrix(displayTitle, PURPLE)

    stop_scrolling_text()

# Aggiungi log di debug per il percorso e i permessi
if __name__ == '__main__':
    print(f"Percorso binario CPP: {CPP_BINARY_PATH}")
    print(f"Permessi di esecuzione: {os.access(CPP_BINARY_PATH, os.X_OK)}")