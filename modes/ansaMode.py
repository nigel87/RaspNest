import feedparser
import time

# RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
RSS_FEED_URL = "https://www.balkanweb.com/feed/"


def read_ansa_news():
    feed = feedparser.parse(RSS_FEED_URL)

    if "title" in feed.feed:
        print("Feed Title:", feed.feed.title)

    for entry in feed.entries:
        if "title" in entry:
            print("Title:", entry.title)


while True:
    read_ansa_news()
    time.sleep(600)  # Fetch and print news every 10 minutes
