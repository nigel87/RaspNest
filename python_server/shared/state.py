import threading

# Global state variables for Context-Aware Action Button and main thread synchronization
is_news_scrolling = False
current_news_entry = None  # Stores the currently scrolling RSS entry dictionary with 'title' and 'summary'

# Music playback state variables
is_music_playing = False
music_title = ""
music_artist = ""

# Thread lock for safe concurrent access
state_lock = threading.Lock()

