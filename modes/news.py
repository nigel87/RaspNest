import os
import time
import threading
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text
import feedparser

BASE_DISPLAY_TIME = 2
SCALE_FACTOR = 0.135
CPP_BINARY_FOLDER = os.path.join(os.path.dirname(__file__), '../c')

def calculate_display_time(text):
    text_length = len(text)
    display_time = int(BASE_DISPLAY_TIME + (text_length * SCALE_FACTOR))
    return display_time

def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    feed = feedparser.parse(rss_feed_url)
    cpp_binary = os.path.join(CPP_BINARY_FOLDER, 'text-scroller')
    
    if "title" in feed.feed:
        title = feed.feed.title
        text_color = "255,0,0"
        # Display the title on the LED matrix
        args = [cpp_binary, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'), title,
               '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
               '--led-slowdown-gpio=4',
               '-C', text_color]
        start_scrolling_text(args)
        time.sleep(calculate_display_time(title))
        stop_scrolling_text()

    for entry in feed.entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title
            # Display the entry title on the LED matrix
            args = [cpp_binary, '-f', os.path.join(CPP_BINARY_FOLDER, '../fonts/9x18.bdf'), entry_title,
                    '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
                    '--led-slowdown-gpio=4']
            start_scrolling_text(args)

            display_time = calculate_display_time(entry_title)
            start_time = time.time()

            # Wait for calculated display time or until stop event is set
            while not stop_event.is_set() and (time.time() - start_time) < display_time:
                time.sleep(1)
            
            stop_scrolling_text()
