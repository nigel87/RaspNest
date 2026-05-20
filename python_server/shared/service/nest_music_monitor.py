import time
import threading
import logging
import requests
import pychromecast
from python_server.shared.constants import GOOGLE_NEST_MINI_NAME, AUTO_RESUME_MODE, TEMP_ALBUM_ART_PATH

def download_album_art(url):
    """
    Downloads album art from the given URL and saves it to a local temporary path.
    """
    try:
        logging.info(f"Downloading YouTube Music album art from: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with open(TEMP_ALBUM_ART_PATH, 'wb') as f:
                f.write(response.content)
            logging.info(f"Album art downloaded successfully to: {TEMP_ALBUM_ART_PATH}")
            return TEMP_ALBUM_ART_PATH
        else:
            logging.warning(f"Failed to download album art. HTTP status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading album art: {e}")
    return None

class NestMediaStatusListener:
    def __init__(self, cast_device, display_service):
        self.cast_device = cast_device
        self.display_service = display_service
        self.current_title = None
        self.current_artist = None
        self.is_playing = False

    def new_media_status(self, status):
        """
        Callback triggered whenever Nest Mini media state changes.
        """
        player_state = getattr(status, 'player_state', 'UNKNOWN')
        logging.debug(f"Nest Mini player state updated: {player_state}")

        if player_state == 'PLAYING':
            title = getattr(status, 'title', None)
            artist = getattr(status, 'artist', None)
            images = getattr(status, 'images', [])
            image_url = images[0].url if images else None

            # Filter or log updates
            logging.info(f"Nest Mini is playing: '{title}' by '{artist}'")

            # Check if this is a new track or if the display service isn't currently in YouTube Music mode (10)
            if (self.display_service.current_mode != 10 or 
                title != self.current_title or 
                artist != self.current_artist):
                
                self.current_title = title
                self.current_artist = artist
                self.is_playing = True

                # Download album cover
                album_art_local_path = None
                if image_url:
                    album_art_local_path = download_album_art(image_url)

                # Programmatically switch matrix display mode
                logging.info(f"Triggering YouTube Music display mode for song: '{title}'")
                self.display_service.trigger_mode_change(
                    mode_id=10,
                    text=title or "Unknown Title",
                    artist=artist or "Unknown Artist",
                    image_path=album_art_local_path
                )
        else:
            # If the speaker goes paused or idle and we were previously playing, revert to resume mode
            if self.is_playing:
                logging.info(f"Nest Mini playback is stopped/paused (State: {player_state}). Reverting to default mode.")
                self.is_playing = False
                self.current_title = None
                self.current_artist = None
                
                # Revert display back to standard main dashboard rotation
                self.display_service.trigger_mode_change(mode_id=AUTO_RESUME_MODE)

def start_monitoring(display_service):
    """
    Initializes and starts the Google Cast background monitoring daemon.
    Runs discovery in a retry loop to prevent blocking server startup.
    """
    def monitor_thread_loop():
        logging.info("Starting Google Nest Mini discovery service...")
        
        while True:
            browser = None
            try:
                # Discover local Cast devices
                chromecasts, browser = pychromecast.get_chromecasts()
                
                # Find the one matching GOOGLE_NEST_MINI_NAME
                cast = next((cc for cc in chromecasts if cc.name == GOOGLE_NEST_MINI_NAME), None)
                
                if cast:
                    logging.info(f"Found Google Cast device '{GOOGLE_NEST_MINI_NAME}' at {cast.cast_info.host}:{cast.cast_info.port}")
                    
                    # Connect to device
                    cast.wait()
                    logging.info(f"Connected to Nest Mini: {cast.name}")
                    
                    # Register media status listener
                    listener = NestMediaStatusListener(cast, display_service)
                    cast.media_controller.register_status_listener(listener)
                    
                    # Keep the connection alive and verify it periodically
                    while True:
                        time.sleep(10)
                        # Heartbeat check
                        _ = cast.status
                        
                else:
                    logging.warning(f"Google Cast device '{GOOGLE_NEST_MINI_NAME}' not found on local network. Retrying in 15 seconds...")
                    pychromecast.discovery.stop_discovery(browser)
                    browser = None
                    time.sleep(15)
                    
            except Exception as e:
                logging.error(f"Error in Nest Monitor connection/discovery loop: {e}. Reconnecting in 15 seconds...")
                if browser:
                    try:
                        pychromecast.discovery.stop_discovery(browser)
                    except Exception:
                        pass
                time.sleep(15)

    # Launch as a background daemon thread
    daemon = threading.Thread(target=monitor_thread_loop, name="NestMusicMonitor", daemon=True)
    daemon.start()
    logging.info("NestMusicMonitor daemon thread started.")
