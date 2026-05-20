#!/usr/bin/env python3
"""
Temporary diagnostic script to inspect the available fields on a pychromecast Chromecast object.
"""
import sys

try:
    import pychromecast
except ImportError:
    print("pychromecast is not installed.")
    sys.exit(1)

print("Scanning for local Cast devices...")
chromecasts, browser = pychromecast.get_chromecasts()

# Stop discovery browser to release resources
pychromecast.discovery.stop_discovery(browser)

if not chromecasts:
    print("No Cast devices found on the network.")
    sys.exit(0)

cc = chromecasts[0]
print(f"\n🔍 Inspecting the first discovered Chromecast object of type: {type(cc)}")
print("-" * 50)

# Check all available fields using reflection
print("Available attributes & properties:")
for attr in sorted(dir(cc)):
    if not attr.startswith('_'):
        try:
            val = getattr(cc, attr)
            # Print value summary
            print(f"  • {attr}: {type(val).__name__} = {repr(val)[:80]}")
        except Exception as e:
            print(f"  • {attr}: [Error reading: {e}]")

print("-" * 50)
