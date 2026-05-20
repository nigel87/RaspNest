import os
import time
import subprocess
import logging
from python_server.shared.controller.matrix_controller import display_on_matrix, stop_scrolling_text
from python_server.shared.constants import CPP_BINARY_FOLDER, GOLD

def run(song_title, artist, album_art_path, stop_event):
    """
    Displays YouTube Music playback details on the LED matrix.
    Alternates between rendering the album cover and scrolling the song details.
    """
    logging.info(f"Starting YouTube Music display mode for: {song_title} by {artist}")
    
    # Ensure any previous animations are fully stopped
    stop_scrolling_text()

    cpp_image_viewer = os.path.join(CPP_BINARY_FOLDER, 'led-image-viewer')

    while not stop_event.is_set():
        # --- PHASE 1: Render the Album Art ---
        if album_art_path and os.path.exists(album_art_path):
            logging.info(f"Showing album art for {song_title}")
            
            # Command to display the album art centered (-C), showing it for 6 seconds (-w 6)
            cmd = [
                "sudo", cpp_image_viewer, 
                "-C",          # Center the image
                "-w", "6",     # Wait/Display for 6 seconds
                album_art_path,
                "--led-no-hardware-pulse", 
                "--led-cols=64", 
                "--led-gpio-mapping=adafruit-hat", 
                "--led-slowdown-gpio=4"
            ]
            
            process = None
            try:
                process = subprocess.Popen(cmd)
                
                # Wait for 6 seconds or until stop_event is set
                start_time = time.time()
                while time.time() - start_time < 6.0:
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                logging.error(f"Error running image viewer in YouTube Music mode: {e}")
            finally:
                if process:
                    if process.poll() is None:
                        process.terminate()
                        process.wait()
                    logging.info("Album art display process stopped.")
                    
        if stop_event.is_set():
            break

        # --- PHASE 2: Scroll the Track Metadata ---
        scroll_text = f"🎵 {song_title} - {artist}"
        logging.info(f"Scrolling track metadata: {scroll_text}")
        
        # Use existing matrix controller logic to display scrolling text
        # This function runs synchronously for the duration of the scroll and respects stop_event
        try:
            display_on_matrix(scroll_text, GOLD, stop_event)
        except Exception as e:
            logging.error(f"Error scrolling track info in YouTube Music mode: {e}")
            time.sleep(1)

        # Clear text scroller before looping
        stop_scrolling_text()
        
    logging.info("YouTube Music display mode stopped.")
