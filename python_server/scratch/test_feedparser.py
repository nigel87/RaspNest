import feedparser

ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

def test_feedparser(name, url):
    print(f"\n--- Testing {name} with feedparser ---")
    try:
        feed = feedparser.parse(url)
        print("Status Code:", feed.get('status', 'N/A'))
        print("Entries count:", len(feed.entries))
        if len(feed.entries) > 0:
            entry = feed.entries[0]
            print("Title:", entry.get('title', 'None'))
            print("Summary:", entry.get('summary', 'None')[:100] + "...")
        else:
            print("No entries found!")
    except Exception as e:
        print("Error:", e)

test_feedparser("ANSA", ANSA_RSS_FEED_URL)
test_feedparser("BalkanWeb", BALLKANWEB_RSS_FEED_URL)
test_feedparser("BBC", BBC_RSS_FEED_URL)
