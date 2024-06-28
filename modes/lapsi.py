
import os
import time
import threading
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text
import feedparser

RSS_FEED_URL = "https://lapsi.al/feed/"

def run(cpp_binary_folder, stop_event):
    # Stop any existing scrolling text
    stop_scrolling_text()

    feed = feedparser.parse(RSS_FEED_URL)
    cpp_binary = os.path.join(cpp_binary_folder, 'text-scroller')
    if "title" in feed.feed:
        title = feed.feed.title
        # Display the title on the LED matrix
        args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), title,
               '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
               '--led-slowdown-gpio=4']
        start_scrolling_text(args)
        time.sleep(3)
        stop_scrolling_text()

    for entry in feed.entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title
            # Display the entry title on the LED matrix
            args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), entry_title,
                    '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
                    '--led-slowdown-gpio=4']
            start_scrolling_text(args)

            # Wait for a few seconds to display each entry
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)
            stop_scrolling_text()
