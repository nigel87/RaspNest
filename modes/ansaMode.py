import feedparser
import time
from utils.display_utils import display_controller


# RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
#RSS_FEED_URL = "https://www.balkanweb.com/feed/"

RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"

def read_ansa_news():
    feed = feedparser.parse(RSS_FEED_URL)

    if "title" in feed.feed:
        title = feed.feed.title
        # Display the title on the LED matrix
        display_controller.display_text(title)

    for entry in feed.entries:
        if "title" in entry:
            entry_title = entry.title
            # Display the entry title on the LED matrix
            display_controller.display_text(entry_title)
            # Wait for a few seconds to display each entry
            time.sleep(3)


while True:
    read_ansa_news()
    time.sleep(600)  # Fetch and display news every 10 minutes
