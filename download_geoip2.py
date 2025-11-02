#!/usr/bin/env python3
"""
Script to download the free GeoLite2 City database from MaxMind.
For use with the bot's GeoIP2 features.
"""

import os
import requests
import tarfile
import tempfile
from pathlib import Path

def download_geolite2_city(target_dir=None):
    """
    Download the GeoLite2 City database.

    Note: Since December 2019 MaxMind requires registration
    to download GeoLite2 databases.

    Alternatives:
    1. Register at https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
    2. Use archived versions from repositories
    3. Use alternative sources
    """
    
    if not target_dir:
        target_dir = os.getenv("LOG_DIR", "/tmp")
    
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    print("📋 GeoLite2 City download info:")
    print("🔗 MaxMind requires registration to download GeoLite2 databases")
    print("📝 Register at: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data")
    print("💾 After registering, obtain the GeoLite2 City .mmdb file")
    print(f"📁 Place the file at: {target_path / 'GeoLite2-City.mmdb'}")
    print()
    
    # Check alternative sources
    alternative_urls = [
        "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb",
        "https://raw.githubusercontent.com/Dreamacro/maxmind-geoip/release/Country.mmdb"
    ]
    
    print("🔄 Attempting download from alternative sources...")
    
    for i, url in enumerate(alternative_urls, 1):
        try:
            print(f"📥 Attempt {i}: {url}")
            response = requests.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                filename = "GeoLite2-City.mmdb" if i == 1 else f"GeoLite2-Alternative-{i}.mmdb"
                filepath = target_path / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Check file size
                file_size = filepath.stat().st_size
                if file_size > 1024 * 1024:  # Larger than 1MB
                    print(f"✅ Downloaded: {filepath} ({file_size / (1024*1024):.1f} MB)")
                    print(f"🔧 Set environment variable: GEOIP2_DB_PATH={filepath}")
                    return str(filepath)
                else:
                    print(f"⚠️ File too small ({file_size} bytes), possible error")
                    filepath.unlink()
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("📋 Manual installation instructions:")
    print("1. Register at https://www.maxmind.com/en/accounts/current/geoip/downloads")
    print("2. Download GeoLite2 City (Binary / gzip)")
    print("3. Extract and place the .mmdb file in the project folder")
    print(f"4. Set GEOIP2_DB_PATH={target_path / 'GeoLite2-City.mmdb'}")
    
    return None

if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else None
    result = download_geolite2_city(target)
    
    if result:
        print(f"\n🎉 Database ready to use: {result}")
    else:
        print("\n❌ Automatic download failed. Use manual installation.")
