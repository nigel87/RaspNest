 
import os
import time
import threading
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text
import feedparser

RSS_FEED_URL = "https://lapsi.al/feed/"

def run(cpp_binary_folder):
    feed = feedparser.parse(RSS_FEED_URL)
    cpp_binary = os.path.join(cpp_binary_folder, 'text-scroller')
    if "title" in feed.feed:
        title = feed.feed.title
        # Display the title on the LED matrix
        args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), title,
               '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
               '--led-slowdown-gpio=4']
        threading.Thread(target=start_scrolling_text, args=(args,)).start()
        time.sleep(3)
        stop_scrolling_text()


    for entry in feed.entries:
        if "title" in entry:
            entry_title = entry.title
            # Display the entry title on the LED matrix
            args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), entry_title,
                    '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
                    '--led-slowdown-gpio=4']
            threading.Thread(target=start_scrolling_text, args=(args,)).start()

            # Wait for a few seconds to display each entry
            time.sleep(10)
            stop_scrolling_text()


# if __name__ == '__main__':
#     cpp_binary_folder = os.path.join(os.path.dirname(__file__), '../c')
#     while True:
#         read_ansa_news(cpp_binary_folder)
#         time.sleep(600)  # Fetch and display news every 10 minutes
