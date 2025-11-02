#!/usr/bin/env python3
"""
GeoIP2 auto-updater integration with the bot.
Runs the update scheduler in the background.
"""

import os
import threading
from geoip2_updater import run_scheduler_in_background

def setup_geoip2_auto_updater():
    """
    Configure automatic GeoIP2 database updates.
    Should be called when the bot starts.
    """
    
    # Check whether auto-update should be enabled
    auto_update_enabled = os.getenv("GEOIP2_AUTO_UPDATE", "true").lower() == "true"
    
    if not auto_update_enabled:
        print("🔕 GeoIP2 auto-update disabled (GEOIP2_AUTO_UPDATE=false)")
        return None
    
    try:
        # Start the scheduler in a background thread
        scheduler_thread = run_scheduler_in_background()
        print("✅ GeoIP2 auto-update started")
        return scheduler_thread
    except Exception as e:
        print(f"❌ Failed to start GeoIP2 auto-update: {e}")
        return None

def get_geoip2_status():
    """Return GeoIP2 database status"""
    from geoip2_updater import load_update_info
    
    info = load_update_info()
    if info.get("last_update"):
        return {
            "enabled": True,
            "last_update": info["last_update"][:19],
            "next_update": info.get("next_update", "N/A")[:19],
            "file_path": info.get("current_db_path"),
            "file_size_mb": round(info.get("file_size", 0) / (1024*1024), 1),
            "source": info.get("source_name", "N/A")
        }
    else:
        return {
            "enabled": False,
            "error": "Database not found"
        }

if __name__ == "__main__":
    # Integration test
    print("🧪 Testing GeoIP2 integration...")
    
    status = get_geoip2_status()
    print(f"📊 Status: {status}")
    
    if status["enabled"]:
        print("✅ GeoIP2 is ready to use")
    else:
        print("⚠️ GeoIP2 requires setup")

        # Start the auto-updater for initial download
        print("🔄 Starting auto-updater...")
        thread = setup_geoip2_auto_updater()

        if thread:
            print("✅ Auto-updater started in background")
        else:
            print("❌ Failed to start auto-updater")
