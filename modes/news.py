import os
import time
import threading
from python_server.scrolling_text_controller import stop_scrolling_text, display_on_matrix
import feedparser
from python_server.constants import RED, GOLD






def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    feed = feedparser.parse(rss_feed_url)
    
    if "title" in feed.feed:
        title = feed.feed.title
        display_on_matrix(title, RED)
        stop_scrolling_text()

    for entry in feed.entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title            
            display_on_matrix(entry_title,GOLD)

            # Wait for calculated display time or until stop event is set
           # while not stop_event.is_set() and (time.time() - start_time) < display_time:
           #     time.sleep(1)
            
            stop_scrolling_text()
