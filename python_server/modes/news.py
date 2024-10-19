import os
import time
import threading
from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix, run_clock_with_scrolling_text
import feedparser
from python_server.shared.constants import RED, GOLD, GREEN

def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    feed = feedparser.parse(rss_feed_url)
    
    if "title" in feed.feed:
        title = feed.feed.title
        run_clock_with_scrolling_text(title,GREEN,RED,stop_event)
        if stop_event.is_set():
            return
        stop_scrolling_text()

    for entry in feed.entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title
            run_clock_with_scrolling_text(entry_title,GREEN,GOLD, stop_event)
            if stop_event.is_set():
                break
            stop_scrolling_text()