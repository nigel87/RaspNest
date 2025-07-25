
import requests
import logging
from python_server.shared.constants import  CITY, WEATHER_BASE_URL, ZIP_CODE
from python_server.shared.service.secret import WEATHER_API_KEY


def get_weather(city, zip_code):
    params = {
        "q": f"{city},{zip_code}",
        "appid": WEATHER_API_KEY,
        "units": "metric"  # Use Celsius for temperature
    }

    response = requests.get(WEATHER_BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logging.error("Failed to retrieve weather data")
        return "N/A"
    

def get_weather_rome():
    return get_weather(CITY, ZIP_CODE)





