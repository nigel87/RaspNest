import os
import requests
import time
import logging

# API_KEY = os.environ.get("API_KEY")
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
        logging.info(f"Temperature in {city} ({zip_code}): {temperature}°C")
    else:
        print("Failed to retrieve weather data")

while True:
    get_weather("Rome", "IT")
    time.sleep(600)  # Fetch weather every 10 minutes
