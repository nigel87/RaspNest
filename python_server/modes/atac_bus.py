import time
import logging
from python_server.shared.controller.matrix_controller import stop_scrolling_text, run_clock_with_scrolling_text
from python_server.shared.service.atac_service import fetch_atac_arrivals
from python_server.shared.constants import GREEN, GOLD, RED

def run(stop_event):
    """
    Runs the ATAC Roma Bus Mode (Mode 11).
    Displays a live clock on the top half of the LED matrix
    and scrolls real-time bus arrivals for stop 74029 underneath.
    
    Refreshes prediction data before each scroll loop.
    """
    logging.info("[ATAC Mode] Starting ATAC bus arrivals display...")
    stop_scrolling_text()
    
    stop_id = "74029"
    
    while not stop_event.is_set():
        stop_name, arrivals = fetch_atac_arrivals(stop_id)
        
        if arrivals is not None:
            if not arrivals:
                scroll_text = f"{stop_name}: Nessun bus"
            else:
                # E.g. "Bullicante/Canosa || 409: 5 Ferm. (9') - n409: Nessun autobus"
                scroll_text = "  -  ".join([f"{arr['line']}: {arr['prediction']}" for arr in arrivals])
                # Capitalize stop name a bit shorter for small LED screens
                short_name = stop_name.split("/")[0] if "/" in stop_name else stop_name
                scroll_text = f"{short_name} || {scroll_text}"
        else:
            scroll_text = "ATAC: Errore connessione"
            
        logging.info(f"[ATAC Mode] Scrolling text: '{scroll_text}'")
        
        # Display the live clock in GREEN, and scroll the bus info in GOLD below it.
        # This function naturally blocks for the time needed to scroll the text completely once.
        run_clock_with_scrolling_text(scroll_text, GOLD, GREEN, stop_event)
        
        if stop_event.is_set():
            break
            
        # Give a small 1s break before fetching fresh data for the next scroll loop
        time.sleep(1)
        
    logging.info("[ATAC Mode] Stopped ATAC bus arrivals display.")
    stop_scrolling_text()
