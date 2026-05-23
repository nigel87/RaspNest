import requests
import re

def test_session():
    r = requests.get("https://romamobile.it/?start_address=74029&Submit=Cerca", headers={
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    })
    print("Status:", r.status_code)
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

if __name__ == "__main__":
    test_session()
