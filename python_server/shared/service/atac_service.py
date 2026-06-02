import requests
import time
import logging
from google.transit import gtfs_realtime_pb2

def fetch_atac_arrivals(stop_id="74029"):
    """
    Fetches real-time bus arrivals for a given stop from Roma Servizi per la Mobilità's GTFS-RT feed.
    Uses official protocol buffer parsing for high reliability and extremely low resource usage.
    Includes 3 retries with a 5-second timeout to handle transient connection drops.
    
    Args:
        stop_id (str): 5-digit bus stop identifier (e.g. '74029' for Bullicante/Canosa)
    Returns:
        tuple: (stop_name, list of dicts with 'line' and 'prediction') or (None, None)
    """
    url = "https://romamobilita.it/wp-content/uploads/shared/rome_rtgtfs_trip_updates_feed.pb"
    
    # Simple dictionary of known stops to save resources
    known_stops = {
        "74029": "Bullicante/Canosa"
    }
    stop_name = known_stops.get(stop_id, f"Fermata {stop_id}")
    
    retries = 3
    timeout = 5
    
    for attempt in range(retries):
        try:
            logging.info(f"[ATAC] Fetching GTFS-RT feed for stop {stop_id} (attempt {attempt + 1}/{retries})...")
            res = requests.get(url, timeout=timeout)
            if res.status_code != 200:
                logging.warning(f"[ATAC] Attempt {attempt + 1} failed. Status code: {res.status_code}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return None, None
            
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(res.content)
            
            current_time = time.time()
            arrivals = []
            
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip_update = entity.trip_update
                    route_id = trip_update.trip.route_id
                    
                    for stop_update in trip_update.stop_time_update:
                        if stop_update.stop_id == stop_id:
                            arr_time = None
                            if stop_update.HasField('arrival'):
                                arr_time = stop_update.arrival.time
                            elif stop_update.HasField('departure'):
                                arr_time = stop_update.departure.time
                            
                            if arr_time is None:
                                continue
                                
                            # Calculate exact remaining minutes
                            wait_time_secs = arr_time - current_time
                            wait_time_mins = int(round(wait_time_secs / 60.0))
                            
                            # Filter out arrivals that are too far in the past
                            if wait_time_mins < -1:
                                continue
                                
                            if wait_time_mins <= 0:
                                prediction = "a tempo"
                            else:
                                prediction = f"{wait_time_mins} min"
                                
                            arrivals.append({
                                "line": route_id,
                                "prediction": prediction,
                                "wait_time": wait_time_mins
                            })
                            
            # Sort arrivals by wait time (ascending)
            arrivals.sort(key=lambda x: x["wait_time"])
            
            # Remove helper wait_time key to match the expected format
            for arr in arrivals:
                arr.pop("wait_time", None)
                
            logging.info(f"[ATAC] Found {len(arrivals)} bus lines for stop {stop_name}.")
            return stop_name, arrivals
            
        except Exception as e:
            logging.warning(f"[ATAC] Attempt {attempt + 1} raised an exception: {e}")
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"[ATAC] All {retries} attempts failed to fetch predictions.")
                return None, None

