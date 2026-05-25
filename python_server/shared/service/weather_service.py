
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

    response = requests.get(WEATHER_BASE_URL, params=params, timeout=5)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logging.error("Failed to retrieve weather data")
        return "N/A"
    

def get_weather_rome():
    return get_weather(CITY, ZIP_CODE)


def get_tomorrow_weather(city, zip_code):
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": f"{city},{zip_code}",
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "cnt": 16
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Tomorrow (24 hours from now) is index 8 (8 * 3 hours)
            tomorrow_item = data['list'][8] if len(data.get('list', [])) > 8 else data['list'][0]
            temp = round(tomorrow_item['main']['temp'])
            descr = tomorrow_item['weather'][0]['main']
            
            # Translate common OpenWeatherMap conditions to short 4-char text
            weather_map = {
                "Clear": "Sole",
                "Clouds": "Nubi",
                "Rain": "Piog",
                "Snow": "Neve",
                "Thunderstorm": "Temp",
                "Drizzle": "Piov",
                "Mist": "Nebb",
                "Fog": "Nebb"
            }
            short_descr = weather_map.get(descr, descr[:4])
            return f"{short_descr} {temp}C"
    except Exception as e:
        logging.error(f"Failed to retrieve tomorrow's weather forecast: {e}")
    return "ND"


def get_tomorrow_weather_rome():
    return get_tomorrow_weather(CITY, ZIP_CODE)






