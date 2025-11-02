#!/usr/bin/env python3
"""
Automatic update of the GeoIP2 database.
Runs weekly to refresh the database.
"""

import os
import sys
import json
import time
import requests
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# File to store last update info
UPDATE_INFO_FILE = "geoip2_update_info.json"

def load_update_info():
    """Load information about the last update"""
    try:
        if os.path.exists(UPDATE_INFO_FILE):
            with open(UPDATE_INFO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load update info: {e}")
    
    return {
        "last_update": None,
        "next_update": None,
        "download_count": 0,
        "current_db_path": None,
        "file_size": 0
    }

def save_update_info(info):
    """Save information about the last update"""
    try:
        with open(UPDATE_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save update info: {e}")

def download_geoip2_database(force_update=False):
    """
    Download the GeoIP2 database with a check if update is needed
    """
    info = load_update_info()
    
    # Check if update is needed
    if not force_update and info.get("last_update"):
        last_update = datetime.fromisoformat(info["last_update"])
        if datetime.now() - last_update < timedelta(days=7):
            print(f"📊 Database is up-to-date. Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            return info.get("current_db_path")
    
    target_dir = os.getenv("LOG_DIR", "/app/data")  # Use /app/data for Docker, /tmp for local
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    print(f"🔄 Updating GeoIP2 database... (attempt #{info['download_count'] + 1})")
    print(f"📁 Target directory: {target_path}")
    
    # Alternative sources (updated list)
    alternative_urls = [
        {
            "url": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb",
            "name": "P3TERX Mirror",
            "filename": "GeoLite2-City.mmdb"
        },
        {
            "url": "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb",
            "name": "Loyalsoldier Country",
            "filename": "GeoLite2-Country.mmdb"
        },
        {
            "url": "https://github.com/Dreamacro/maxmind-geoip/raw/release/Country.mmdb",
            "name": "Dreamacro Country",
            "filename": "GeoLite2-Country-Alt.mmdb"
        }
    ]
    
    for i, source in enumerate(alternative_urls, 1):
        try:
            print(f"📥 Attempt {i}/{len(alternative_urls)}: {source['name']}")
            print(f"   URL: {source['url']}")
            
            # Download with progress
            response = requests.get(source['url'], timeout=60, stream=True)
            
            if response.status_code == 200:
                filepath = target_path / source['filename']
                temp_filepath = target_path / f"{source['filename']}.tmp"
                
                # Get total size
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                print(f"   📦 File size: {total_size / (1024*1024):.1f} MB")
                
                with open(temp_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Simple progress indicator
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\r   ⏳ Downloaded: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='')
                
                print()  # Newline after progress
                
                # Check downloaded file size
                file_size = temp_filepath.stat().st_size
                if file_size > 1024 * 1024:  # Larger than 1MB
                    # Move temp file to final
                    if filepath.exists():
                        filepath.unlink()
                    temp_filepath.rename(filepath)
                    
                    print(f"✅ Successfully downloaded: {filepath} ({file_size / (1024*1024):.1f} MB)")
                    
                    # Update info
                    now = datetime.now()
                    info.update({
                        "last_update": now.isoformat(),
                        "next_update": (now + timedelta(days=7)).isoformat(),
                        "download_count": info.get("download_count", 0) + 1,
                        "current_db_path": str(filepath),
                        "file_size": file_size,
                        "source_name": source['name'],
                        "source_url": source['url']
                    })
                    save_update_info(info)
                    
                    # Set environment variable
                    os.environ["GEOIP2_DB_PATH"] = str(filepath)
                    
                    print(f"🔧 GEOIP2_DB_PATH set to: {filepath}")
                    print(f"📅 Next update: {info['next_update'][:19]}")
                    
                    return str(filepath)
                else:
                    print(f"⚠️ File too small ({file_size} bytes), possible error")
                    temp_filepath.unlink()
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error downloading from {source['name']}: {e}")
    
    print("\n❌ All sources are unavailable")
    return None

def check_and_update_database():
    """Check and update the database if necessary"""
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking GeoIP2 updates...")
    
    try:
        result = download_geoip2_database()
        if result:
            print("✅ GeoIP2 database is up-to-date")
            
            # Verify that the database works
            try:
                import geoip2.database
                with geoip2.database.Reader(result) as reader:
                    test_response = reader.city('8.8.8.8')
                    print(f"🧪 Database test: {test_response.country.name} / {test_response.city.name}")
            except Exception as e:
                print(f"⚠️ Database test failed: {e}")
        else:
            print("❌ Failed to update the database")
    except Exception as e:
        print(f"❌ Error while checking updates: {e}")

def start_scheduler():
    """Start the update scheduler"""
    print("🚀 Starting GeoIP2 update scheduler...")
    
    # Schedule weekly update every Sunday at 03:00
    schedule.every().sunday.at("03:00").do(check_and_update_database)
    
    # Also run a check on startup
    print("🔄 Performing initial check...")
    check_and_update_database()
    
    print("📅 Scheduler configured: updates every Sunday at 03:00")
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

def run_scheduler_in_background():
    """Run the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("🔄 GeoIP2 scheduler started in background")
    return scheduler_thread

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage the GeoIP2 database")
    parser.add_argument("--force", action="store_true", help="Force update")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show status")
    
    args = parser.parse_args()
    
    if args.status:
        info = load_update_info()
        if info.get("last_update"):
            print(f"📊 GeoIP2 database status:")
            print(f"   Last update: {info['last_update'][:19]}")
            print(f"   Next update: {info.get('next_update', 'N/A')[:19]}")
            print(f"   Download count: {info.get('download_count', 0)}")
            print(f"   Current file: {info.get('current_db_path', 'N/A')}")
            print(f"   File size: {info.get('file_size', 0) / (1024*1024):.1f} MB")
            print(f"   Source: {info.get('source_name', 'N/A')}")
        else:
            print("📊 GeoIP2 database not found")
    elif args.daemon:
        start_scheduler()
    else:
        download_geoip2_database(force_update=args.force)
