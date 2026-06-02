import requests
import re

def fetch_atac_arrivals(1{stop_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch. Status code: {response.status_code}")
            return None
        
        html = response.text
        html = html.replace("&#39;", "'").replace("&amp;", "&")
        
        # Find the stop name
        stop_name_match = re.search(r'<h2>(.*?)</h2>', html)
        stop_name = stop_name_match.group(1).strip() if stop_name_match else "Fermata"
        
        # Regex to find links with class="noa"
        pattern = r'<a class="noa" href="[^"]+">(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        arrivals = []
        for match in matches:
            line_match = re.search(r'<span class="linea">(.*?)</span>', match)
            if not line_match:
                continue
            line = line_match.group(1).strip()
            
            # Clean tag contents
            text_clean = re.sub(r'<[^>]+>', '', match)
            # Remove the line number from the text
            text_clean = text_clean.replace(line, "", 1)
            prediction = " ".join(text_clean.split())
            
            arrivals.append({
                "line": line,
                "prediction": prediction
            })
            
        return stop_name, arrivals
    except Exception as e:
        print(f"Error fetching ATAC data: {e}")
        return None, None

if __name__ == "__main__":
    stop_name, arrivals = fetch_atac_arrivals("74029")
    print(f"\nStop Name: {stop_name}")
    if arrivals:
        for arr in arrivals:
            print(f"Bus {arr['line']}: {arr['prediction']}")
    else:
        print("No arrivals found.")
