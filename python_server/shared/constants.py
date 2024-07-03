import os

ANSA_RSS_FEED_URL = "https://www.ansa.it/sito/ansait_rss.xml"
BALLKANWEB_RSS_FEED_URL = "https://www.balkanweb.com/feed/"
LAPSI_RSS_FEED_URL = "https://lapsi.al/feed/"


CITY = 'Rome,IT'
ZIP_CODE = "IT"
TEMP_FILE = "/tmp/current_temperature.txt"
CPP_BINARY_FOLDER = os.path.join(os.path.dirname(__file__), '../../c')
CPP_BINARY_PATH = os.path.join(CPP_BINARY_FOLDER, 'text-scroller')

FOOTBALL_BASE_URL = 'https://api.football-data.org/v2/'
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
STOCK_MARKET_BASE_URL = "https://www.alphavantage.co/query"


# Define the dictionary mapping color names to their RGB values
colors = {
    "red": "255,0,0",
    "green": "0,255,0",
    "blue": "0,0,255",
    "white": "255,255,255",
    "black": "0,0,0",
    "yellow": "255,255,0",
    "cyan": "0,255,255",
    "magenta": "255,0,255",
    "orange": "255,165,0",
    "purple": "128,0,128",
    "pink": "255,192,203",
    "brown": "165,42,42",
    "grey": "128,128,128",
    "lime": "0,255,0",
    "navy": "0,0,128",
    "gold": "255,215,0"
}

RED = colors["red"]
GREEN = colors["green"]
BLUE = colors["blue"]
WHITE = colors["white"]
BLACK = colors["black"]
YELLOW = colors["yellow"]
CYAN = colors["cyan"]
MAGENTA = colors["magenta"]
ORANGE = colors["orange"]
PURPLE = colors["purple"]
PINK = colors["pink"]
BROWN = colors["brown"]
GREY = colors["grey"]
LIME = colors["lime"]
NAVY = colors["navy"]
GOLD = colors["gold"]