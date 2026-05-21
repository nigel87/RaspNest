import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python_server.shared.service.atac_service import fetch_atac_arrivals

if __name__ == "__main__":
    stop_name, arrivals = fetch_atac_arrivals("74029")
    print(f"\nStop Name: {stop_name}")
    if arrivals:
        for arr in arrivals:
            print(f"Bus {arr['line']}: {arr['prediction']}")
    else:
        print("No arrivals found.")
