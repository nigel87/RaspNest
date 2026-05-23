import urllib.request
import re

ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

def test_feed(name, url):
    print(f"\n--- Testing {name} Feed ({url}) ---")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8', errors='ignore')
            
            # Trova il primo blocco <item>
            item_match = re.search(r'<item>(.*?)</item>', xml, re.DOTALL)
            if not item_match:
                # Prova con <entry> (Atom feed)
                item_match = re.search(r'<entry>(.*?)</entry>', xml, re.DOTALL)
                
            if item_match:
                item_content = item_match.group(1)
                title = re.search(r'<title>(.*?)</title>', item_content, re.DOTALL)
                description = re.search(r'<description>(.*?)</description>', item_content, re.DOTALL)
                summary = re.search(r'<summary>(.*?)</summary>', item_content, re.DOTALL)
                
                print("Title:", title.group(1).strip() if title else "None")
                print("Description:", description.group(1).strip()[:200] + "..." if description else "None")
                print("Summary:", summary.group(1).strip()[:200] + "..." if summary else "None")
            else:
                print("No items or entries found in XML!")
    except Exception as e:
        print(f"Error testing feed: {e}")

test_feed("ANSA", ANSA_RSS_FEED_URL)
test_feed("BalkanWeb", BALLKANWEB_RSS_FEED_URL)
test_feed("BBC", BBC_RSS_FEED_URL)
