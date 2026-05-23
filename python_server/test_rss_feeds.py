import feedparser

ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

def test_feed(name, url):
    print(f"\n--- Testing {name} Feed ({url}) ---")
    feed = feedparser.parse(url)
    if not feed.entries:
        print("No entries found!")
        return
    
    # Prendi la prima entry
    entry = feed.entries[0]
    print("Title:", entry.get("title", "No Title"))
    print("Summary/Description keys:", [k for k in entry.keys() if "summary" in k or "description" in k])
    print("Summary value:", entry.get("summary", entry.get("description", "No Summary/Description value")))

test_feed("ANSA", ANSA_RSS_FEED_URL)
test_feed("BalkanWeb", BALLKANWEB_RSS_FEED_URL)
test_feed("BBC", BBC_RSS_FEED_URL)
