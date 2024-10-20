import os
import time
import threading
from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix, run_clock_with_scrolling_text
import feedparser
from python_server.shared.constants import RED, GOLD, GREEN

# Set to keep track of displayed news titles
displayed_news = set()

def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    feed = feedparser.parse(rss_feed_url)
    while not stop_event.is_set():
        if "title" in feed.feed:
            title = feed.feed.title
            run_clock_with_scrolling_text(title,GREEN,RED,stop_event)
            if stop_event.is_set():
                return
            stop_scrolling_text()
        for entry in feed.entries:
            if stop_event.is_set():
                break

            # Check if the entry has a title and is new
            if "title" in entry:
                entry_title = entry.title
                if entry_title not in displayed_news:
                    # Display the new news title
                    run_clock_with_scrolling_text(entry_title, GREEN, GOLD, stop_event)

                    # Mark this title as displayed
                    displayed_news.add(entry_title)

                    # Stop scrolling text after displaying the entry
                    if stop_event.is_set():
                        break
                    stop_scrolling_text()