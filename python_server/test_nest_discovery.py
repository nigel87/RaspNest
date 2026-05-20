#!/usr/bin/env python3
"""
Diagnostic script to verify local network Google Cast device discovery.
Run this directly on your Raspberry Pi (or your Mac if on the same network)
to check if your 'Nest mini' is visible and see its active playback status.
"""
import sys
import time

try:
    import pychromecast
except ImportError:
    print("Error: 'pychromecast' package is not installed.")
    print("Please install it on this device using:")
    print("  pip3 install pychromecast")
    sys.exit(1)

TARGET_NAME = "Nest mini"

print("Scanning local network for Google Cast / Nest devices...")
print("This may take up to 5-10 seconds...")

# Discover devices
chromecasts, browser = pychromecast.get_chromecasts()

if not chromecasts:
    print("\n❌ NO CAST DEVICES DISCOVERED ON THE LOCAL NETWORK.")
    print("Suggestions:")
    print("  1. Make sure this device is on the EXACT same Wi-Fi subnet as your Nest speaker.")
    print("  2. Check if mDNS / IGMP Snooping is enabled on your Wi-Fi router (required for discovery).")
    print("  3. Double-check if the speaker is powered on and connected to Google Home.")
    sys.exit(1)

print(f"\n🔍 Discovered {len(chromecasts)} Google Cast device(s):")
target_found = None

for cc in chromecasts:
    friendly_name = cc.name
    model_name = cc.model_name
    host = cc.cast_info.host
    port = cc.cast_info.port
    print(f"  • Name: '{friendly_name}' | Model: {model_name} | Address: {host}:{port}")
    if friendly_name == TARGET_NAME:
        target_found = cc

if target_found:
    print(f"\n✅ SUCCESS! Found target device '{TARGET_NAME}'!")
    print("Attempting to connect and read status...")
    try:
        target_found.wait()
        print("  - Connection established!")
        
        # Give the asynchronous media controller thread a moment to sync status
        time.sleep(1.0)
        
        status = target_found.status
        print(f"  - System Volume: {status.volume_level * 100:.1f}%")
        print(f"  - Active App: {target_found.app_display_name or 'None (Idle)'}")
        
        media_status = target_found.media_controller.status
        print(f"  - Media Player State: {media_status.player_state}")
        
        if media_status.player_state == "PLAYING":
            print(f"  - Track: '{media_status.title}'")
            print(f"  - Artist: '{media_status.artist}'")
            if media_status.images:
                print(f"  - Album Art URL: {media_status.images[0].url}")
        else:
            print("  - Play some YouTube Music on your speaker and run this script again to see metadata!")
    except Exception as e:
        print(f"❌ Error connecting to device status: {e}")
else:
    print(f"\n⚠️ Target device '{TARGET_NAME}' was NOT found.")
    print(f"Please verify the exact friendly name matches the Google Home app and update constants.py if necessary.")

# Stop discovery browser to release resources
pychromecast.discovery.stop_discovery(browser)

