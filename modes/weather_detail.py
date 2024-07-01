import os
import requests
import subprocess
import time
import threading
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text, display_on_matrix
from python_server.constants import *



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