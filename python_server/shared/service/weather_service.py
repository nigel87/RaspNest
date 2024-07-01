
import requests
from python_server.shared.constants import API_KEY, CITY, ZIP_CODE


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
    

def get_weather_rome():
    return get_weather(CITY, ZIP_CODE)





