import time
import threading
import logging
import requests
import pychromecast
from python_server.shared.constants import GOOGLE_NEST_MINI_NAME, AUTO_RESUME_MODE, TEMP_ALBUM_ART_PATH

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_album_art(url):
    """
    Downloads album art from the given URL and saves it to a local temporary path.
    Bypasses SSL verification (verify=False) to ensure reliability in systemd/root environments.
    """
    try:
        logging.info(f"Downloading YouTube Music album art from: {url}")
        response = requests.get(url, timeout=5, verify=False)
        if response.status_code == 200:
            with open(TEMP_ALBUM_ART_PATH, 'wb') as f:
                f.write(response.content)
            import os
            logging.info(f"Album art downloaded successfully to: {TEMP_ALBUM_ART_PATH} (Size: {os.path.getsize(TEMP_ALBUM_ART_PATH)} bytes)")
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

        from python_server.shared import state

        if player_state == 'PLAYING':
            title = getattr(status, 'title', None) or "Unknown Title"
            artist = getattr(status, 'artist', None) or "Unknown Artist"
            images = getattr(status, 'images', [])
            image_url = images[0].url if images else None

            logging.info(f"Nest Mini is playing: '{title}' by '{artist}'")

            # Always update global music state
            with state.state_lock:
                state.is_music_playing = True
                state.music_title = title
                state.music_artist = artist

            # Download album cover and downscale to 32x32 raw RGB bytes
            album_art_local_path = None
            if image_url:
                album_art_local_path = download_album_art(image_url)
                if album_art_local_path:
                    try:
                        from PIL import Image
                        im = Image.open(album_art_local_path)
                        im = im.resize((32, 32)).convert('RGB')
                        raw_path = "/var/weather/album_art_raw.bin"
                        import os
                        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                        with open(raw_path, "wb") as f:
                            f.write(im.tobytes())
                        logging.info(f"Nest Music Monitor: Downscaled 32x32 album art written to {raw_path}")
                    except Exception as e:
                        logging.error(f"Nest Music Monitor: Failed to downscale/save album art: {e}")

            # If current mode is 8 (Static Dashboard), let it handle the music state internally
            if self.display_service.current_mode == 8:
                logging.info("Nest Music Monitor: System is in Mode 8. Letting the dashboard handle music layout dynamically.")
                self.current_title = title
                self.current_artist = artist
                self.is_playing = True
            else:
                # Trigger Mode 10 if we are in another mode or if it's a new track
                if (self.display_service.current_mode != 10 or 
                    title != self.current_title or 
                    artist != self.current_artist):
                    
                    self.current_title = title
                    self.current_artist = artist
                    self.is_playing = True

                    logging.info(f"Triggering YouTube Music display mode for song: '{title}'")
                    self.display_service.trigger_mode_change(
                        mode_id=10,
                        text=title,
                        artist=artist,
                        image_path=album_art_local_path
                    )
        else:
            # Revert global music state
            with state.state_lock:
                state.is_music_playing = False
                state.music_title = ""
                state.music_artist = ""

            # If the speaker goes paused or idle and we were previously playing, revert
            if self.is_playing:
                logging.info(f"Nest Mini playback is stopped/paused (State: {player_state}). Reverting to default mode.")
                self.is_playing = False
                self.current_title = None
                self.current_artist = None
                
                # If display is in mode 10, revert back to mode 8
                if self.display_service.current_mode == 10:
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
                    
                    # Store discovered IP in global state
                    from python_server.shared import state
                    with state.state_lock:
                        state.nest_mini_ip = cast.cast_info.host
                        
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
