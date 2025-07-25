import os
import time
import threading
import logging
from python_server.shared.controller.matrix_controller import stop_scrolling_text, run_clock_with_scrolling_text, run_clock_on_matrix_with_timeout
import feedparser
from python_server.shared.constants import RED, GOLD, GREEN, TEMP_FILE
import subprocess
from python_server.shared.service.weather_service import get_weather_rome

# RSS Feed URLs
ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

# Set to keep track of displayed news titles
displayed_news = set()

def run(stop_event):
    stop_scrolling_text()

    rss_feed_urls = [ANSA_RSS_FEED_URL, BALLKANWEB_RSS_FEED_URL, BBC_RSS_FEED_URL]
    new_news_found = False

    # Initial fetch and add all news titles to displayed_news
    for rss_feed_url in rss_feed_urls:
        feed = feedparser.parse(rss_feed_url)
        for entry in feed.entries:
            entry_title = entry.title
            displayed_news.add(entry_title)

    while not stop_event.is_set():
        new_news_found = False  # Reset for each iteration
        logging.info(f"Checking for new news")  # Log check for news each loop

        # Loop through all RSS feeds
        for rss_feed_url in rss_feed_urls:
            feed = feedparser.parse(rss_feed_url)  # Parse feed inside the loop for each feed

            for entry in feed.entries:
                if stop_event.is_set():
                    return  # Exit the loop and function if stop_event is set

                if "title" in entry:
                    entry_title = entry.title
                    if entry_title not in displayed_news:
                        # Display the new news title
                        new_news_found = True
                        display_new_news_three_times(entry_title, stop_event)

                        # Mark this title as displayed
                        displayed_news.add(entry_title)

                        # Stop scrolling text after displaying the entry
                        if stop_event.is_set():
                            return  # Exit function if stop_event is set
                        stop_scrolling_text()

        # If no new news, display clock with weather
        if not new_news_found:
            run_clock_on_matrix_with_timeout(stop_event)
            stop_scrolling_text()
            logging.info("Clock display completed, back to checking news.")

        # Wait for a while before checking for new news again
        time.sleep(0.01)


def display_new_news_three_times(entry_title, stop_event):
    for i in range(3):
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