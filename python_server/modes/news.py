import os
import time
import threading
from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix, run_clock_with_scrolling_text
import feedparser
from python_server.shared.constants import RED, GOLD

def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    feed = feedparser.parse(rss_feed_url)
    
    if "title" in feed.feed:
        title = feed.feed.title
        # run_clock_with_scrolling_text(title, RED,stop_event)
        run_clock_with_scrolling_text(title,stop_event)
        if stop_event.is_set():
            return
        stop_scrolling_text()

    for entry in feed.entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title
            #display_on_matrix(entry_title, GOLD,stop_event)
            run_clock_with_scrolling_text(entry_title, stop_event) # TODO colour
            if stop_event.is_set():
                break
            stop_scrolling_text()