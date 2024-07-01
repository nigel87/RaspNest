import os
from python_server.scrolling_text_controller import display_on_matrix, stop_scrolling_text
from python_server.constants import *
from python_server.shared.weather_service import get_weather_rome


def run(stop_event):
    stop_scrolling_text()
    weather = get_weather_rome()
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
    display_on_matrix(displayTitle, GREEN,stop_event)

    displayTitle = 'Temperatura percepita: ' + str(feels_like) 
    display_on_matrix(displayTitle, YELLOW,stop_event)

    displayTitle = 'Temperature MIN ' + str(temp_min) 
    display_on_matrix(displayTitle, GREEN,stop_event)

    displayTitle = 'Temperature MAX ' + str(temp_max) 
    display_on_matrix(displayTitle, RED,stop_event)

    displayTitle = 'Umidità ' + str(humidity) 
    display_on_matrix(displayTitle, ORANGE,stop_event)

    #displayTitle = 'Rain in 1h' + str(rain1h) 
    #display_on_matrix(displayTitle, BLUE,stop_event)

    #displayTitle = 'Rain in 3h' + str(rain3h) 
    #display_on_matrix(displayTitle, PURPLE,stop_event)

    stop_scrolling_text()

# Aggiungi log di debug per il percorso e i permessi
if __name__ == '__main__':
    print(f"Percorso binario CPP: {CPP_BINARY_PATH}")
    print(f"Permessi di esecuzione: {os.access(CPP_BINARY_PATH, os.X_OK)}")