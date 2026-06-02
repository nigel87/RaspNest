import requests
import re

def test_session():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    }
    
    # Use a session to automatically store and transmit cookies (like sessionid)
    session = requests.Session()
    
    try:
        # Step 1: Establish session by hitting the homepage
        print("Step 1: Accessing homepage...")
        home_res = session.get("https://www.romamobile.it/", headers=headers, timeout=10)
        print("Home Response Status:", home_res.status_code)
        print("Session Cookies:", session.cookies.get_dict())
        
        # Step 2: Fetch the paline endpoint
        print("\nStep 2: Accessing stop paline...")
        url = "https://www.romamobile.it/paline/?cerca=74029"
        r = session.get(url, headers=headers, timeout=10)
        print("Paline Response Status:", r.status_code)
        
        html = r.text
        
        # Cerchiamo il nome della fermata
        stop_name_match = re.search(r'<h2>(.*?)</h2>', html)
        stop_name = stop_name_match.group(1).strip() if stop_name_match else "None"
        print("Stop Name:", stop_name)
        
        # Cerca i link noa
        pattern = r'<a class="noa" href="[^"]+">(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        print("Matches Found:", len(matches))
        
        for match in matches:
            line_match = re.search(r'<span class="linea">(.*?)</span>', match)
            if line_match:
                line = line_match.group(1).strip()
                text_clean = re.sub(r'<[^>]+>', '', match)
                text_clean = text_clean.replace(line, "", 1)
                prediction = " ".join(text_clean.split())
                print(f"Line {line}: {prediction}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_session()
