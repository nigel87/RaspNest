import os
import time
import threading
from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix, run_clock_with_scrolling_text
import feedparser
from python_server.shared.constants import RED, GOLD, GREEN

import requests
import logging

def parse_feed_safely(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            logging.error(f"[News Mode] RSS feed {url} returned HTTP status {res.status_code}")
            return None
        feed = feedparser.parse(res.content)
        if getattr(feed, "bozo", 0) == 1:
            logging.warning(f"[News Mode] RSS feed parser bozo exception for {url}: {feed.bozo_exception}")
        return feed
    except Exception as e:
        logging.error(f"[News Mode] RSS error querying feed {url}: {e}", exc_info=True)
        return None

def run(rss_feed_url, stop_event):
    stop_scrolling_text()

    if rss_feed_url == "all":
        urls = [
            "https://www.ansa.it/sito/ansait_rss.xml",
            "https://www.balkanweb.com/feed/",
            "https://feeds.bbci.co.uk/news/world/rss.xml"
        ]
        entries = []
        for url in urls:
            if stop_event.is_set():
                return
            try:
                feed = parse_feed_safely(url)
                if feed and feed.entries:
                    entries.extend(feed.entries)
            except Exception as e:
                logging.error(f"[News Mode] Exception fetching feed {url}: {e}")
        
        # Display title for the combined feed
        run_clock_with_scrolling_text("All Feeds", GREEN, RED, stop_event)
        if stop_event.is_set():
            return
        stop_scrolling_text()
    else:
        feed = parse_feed_safely(rss_feed_url)
        if feed and feed.feed and "title" in feed.feed:
            title = feed.feed.title
            run_clock_with_scrolling_text(title, GREEN, RED, stop_event)
            if stop_event.is_set():
                return
            stop_scrolling_text()
        entries = feed.entries if feed else []

    for entry in entries:
        if stop_event.is_set():
            break
        if "title" in entry:
            entry_title = entry.title
            run_clock_with_scrolling_text(entry_title, GREEN, GOLD, stop_event)
            if stop_event.is_set():
                break
            stop_scrolling_text()