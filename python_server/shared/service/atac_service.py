import requests
import re
import logging
import time

def fetch_atac_arrivals(stop_id="74029"):
    """
    Fetches real-time bus arrivals for a given stop from romamobile.it.
    No API Key required. Highly efficient regex-based parsing.
    Includes 3 retries with a 5-second timeout to handle transient connection drops.
    
    Args:
        stop_id (str): 5-digit bus stop identifier (e.g. '74029' for Bullicante/Canosa)
    Returns:
        tuple: (stop_name, list of dicts with 'line' and 'prediction') or (None, None)
    """
    url = f"https://romamobile.it/paline/?cerca={stop_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    }
    
    retries = 3
    timeout = 5
    
    for attempt in range(retries):
        try:
            logging.info(f"[ATAC] Fetching predictions for stop {stop_id} (attempt {attempt + 1}/{retries})...")
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                logging.warning(f"[ATAC] Attempt {attempt + 1} failed. Status code: {response.status_code}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                else:
                    return None, None
            
            html = response.text
            # Clean common html entities to ease regex matching and representation
            html = html.replace("&#39;", "'").replace("&amp;", "&").replace("&quot;", '"')
            
            # Extract Stop Name
            stop_name_match = re.search(r'<h2>(.*?)</h2>', html)
            stop_name = stop_name_match.group(1).strip() if stop_name_match else f"Fermata {stop_id}"
            
            # Regex to find links containing the bus line details (class="noa")
            pattern = r'<a class="noa" href="[^"]+">(.*?)</a>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            arrivals = []
            for match in matches:
                line_match = re.search(r'<span class="linea">(.*?)</span>', match)
                if not line_match:
                    continue
                line = line_match.group(1).strip()
                
                # Clean all HTML tags from inside the link to leave only prediction text
                text_clean = re.sub(r'<[^>]+>', '', match)
                # Remove the line identifier (e.g. '409') once at the start of text
                text_clean = text_clean.replace(line, "", 1)
                prediction = " ".join(text_clean.split())
                
                arrivals.append({
                    "line": line,
                    "prediction": prediction
                })
                
            logging.info(f"[ATAC] Found {len(arrivals)} bus lines for stop {stop_name}.")
            return stop_name, arrivals
            
        except Exception as e:
            logging.warning(f"[ATAC] Attempt {attempt + 1} raised an exception: {e}")
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"[ATAC] All {retries} attempts failed to fetch predictions.")
                return None, None

