import time
import logging
from python_server.shared.controller.matrix_controller import stop_scrolling_text, run_clock_with_scrolling_text
from python_server.shared.service.atac_service import fetch_atac_arrivals
from python_server.shared.constants import GREEN, GOLD

# --- CONFIGURATION CONSTANTS ---
# Frequenza di aggiornamento dei dati ATAC: impostare a 30.0 per mezzo minuto, o a 60.0 per un minuto.
CACHE_DURATION = 30.0  # seconds

# Tempo massimo di validità della cache in caso di errori persistenti di connessione.
MAX_CACHE_AGE = 180.0  # seconds (3 minutes)

def run(stop_event):
    """
    Runs the ATAC Roma Bus Mode (Mode 11).
    Displays a live clock on the top half of the LED matrix
    and scrolls real-time bus arrivals for stop 74029 underneath.
    
    Optimized: Caches predictions to avoid overloading the API, 
    and handles transient connection errors by falling back gracefully to the last cached data.
    """
    logging.info("[ATAC Mode] Starting ATAC bus arrivals display with resilient caching...")
    stop_scrolling_text()
    
    stop_id = "74029"
    
    # Caching and rate-limiting state
    last_fetch_time = 0
    cached_scroll_text = None
    last_successful_fetch = 0
    
    while not stop_event.is_set():
        current_time = time.time()
        
        # Check if it's time to fetch fresh data
        if current_time - last_fetch_time >= CACHE_DURATION:

            logging.info("[ATAC Mode] Fetching fresh bus arrivals...")
            stop_name, arrivals = fetch_atac_arrivals(stop_id)
            last_fetch_time = current_time
            
            if arrivals is not None:
                # Successfully fetched data
                last_successful_fetch = current_time
                if not arrivals:
                    cached_scroll_text = f"{stop_name}: Nessun bus"
                else:
                    # E.g. "Bullicante/Canosa || 409: 5 Ferm. (9') - n409: Nessun autobus"
                    scroll_text = "  -  ".join([f"{arr['line']}: {arr['prediction']}" for arr in arrivals])
                    short_name = stop_name.split("/")[0] if "/" in stop_name else stop_name
                    cached_scroll_text = f"{short_name} || {scroll_text}"
                logging.info(f"[ATAC Mode] Fresh data fetched successfully: '{cached_scroll_text}'")
            else:
                # Fetch failed (connection error / timeout)
                logging.warning("[ATAC Mode] Fetch failed. Attempting to use cached data...")
                
        # Determine what to display
        if cached_scroll_text is not None and (current_time - last_successful_fetch < MAX_CACHE_AGE):
            # Display cached data (either fresh or gracefully retained due to transient failure)
            if current_time - last_successful_fetch > CACHE_DURATION:
                # Mark as stale in logs
                logging.info(f"[ATAC Mode] Displaying cached data (Age: {int(current_time - last_successful_fetch)}s): '{cached_scroll_text}'")
            scroll_text_to_display = cached_scroll_text
        else:
            # No cache available, or cache is too old (persistent outage)
            logging.error("[ATAC Mode] No active or fresh cache available. Displaying connection error.")
            scroll_text_to_display = "ATAC: Errore connessione"
            
        # Display the live clock in GREEN, and scroll the bus info in GOLD below it.
        # This function naturally blocks for the time needed to scroll the text completely once (approx. 5-15s).
        run_clock_with_scrolling_text(scroll_text_to_display, GOLD, GREEN, stop_event)
        
        if stop_event.is_set():
            break
            
        # Small break between scroll loop steps to keep CPU usage low
        time.sleep(1)
        
    logging.info("[ATAC Mode] Stopped ATAC bus arrivals display.")
    stop_scrolling_text()
