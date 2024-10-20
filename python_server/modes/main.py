import os
import time
import threading
from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix, \
    run_clock_with_scrolling_text, run_clock_on_matrix
import feedparser
from python_server.shared.constants import RED, GOLD, GREEN, TEMP_FILE
import requests
import subprocess
import time
from python_server.shared.service.weather_service import get_weather_rome


# Set to keep track of displayed news titles
displayed_news = set()

def run(rss_feed_url, stop_event):
    stop_scrolling_text()
    new_news_found = False
    feed = feedparser.parse(rss_feed_url)

    for entry in feed.entries:
        entry_title = entry.title
        displayed_news.add(entry_title)


    while not stop_event.is_set():
        # if "title" in feed.feed:
        #     title = feed.feed.title
        #     run_clock_with_scrolling_text(title,GREEN,RED,stop_event)
        #     if stop_event.is_set():
        #         return
        #     stop_scrolling_text()

        for entry in feed.entries:
            if stop_event.is_set():
                break
            # Check if the entry has a title and is new
            if "title" in entry:
                entry_title = entry.title
                if entry_title not in displayed_news:
                    # Display the new news title
                    new_news_found = True
                    display_new_news_five_times(entry_title, stop_event)

                    # Mark this title as displayed
                    displayed_news.add(entry_title)

                    # Stop scrolling text after displaying the entry
                    if stop_event.is_set():
                        break
                    stop_scrolling_text()
        # If no new news, display clock with weather
        if not new_news_found:
            run_clock_on_matrix(stop_event)

        # Wait for a while before checking for new news again
        time.sleep(60)


def display_new_news_five_times(entry_title, stop_event):
    for i in range(5):
        run_clock_with_scrolling_text(entry_title, GREEN, GOLD, stop_event)


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
        temperature = str(get_weather_rome()["main"]["temp"]) + '°C'
        write_temperature_to_file(temperature)
        for _ in range(600):  # Check stop_event every second for 10 minutes
            if stop_event.is_set():
                break
            time.sleep(1)
