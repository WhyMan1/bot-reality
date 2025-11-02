#!/bin/bash
# Script for setting up GeoIP2 on Ubuntu server

echo "🌍 Setting up GeoIP2 for Ubuntu server..."

# Create directories
sudo mkdir -p /var/lib/geoip
sudo mkdir -p /opt/geoip

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip curl wget

# Install Python packages
pip3 install geoip2 maxminddb schedule

# Download database to system directory
echo "📥 Downloading GeoIP2 database..."
cd /var/lib/geoip

# Use auto-updater
if [ -f "/path/to/bot-reality/geoip2_updater.py" ]; then
    sudo python3 /path/to/bot-reality/geoip2_updater.py --force
else
    # Alternative download
    sudo wget -O GeoLite2-City.mmdb.tmp "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb"
    
    # Check file size
    if [ -s GeoLite2-City.mmdb.tmp ]; then
        sudo mv GeoLite2-City.mmdb.tmp GeoLite2-City.mmdb
        echo "✅ Database downloaded to /var/lib/geoip/GeoLite2-City.mmdb"
    else
        echo "❌ Database download error"
        sudo rm -f GeoLite2-City.mmdb.tmp
        exit 1
    fi
fi

# Set access permissions
sudo chown -R www-data:www-data /var/lib/geoip
sudo chmod -R 644 /var/lib/geoip/*.mmdb

# Create cron job for auto-update
echo "⏰ Setting up auto-update..."
CRON_JOB="0 3 * * 0 cd /path/to/bot-reality && python3 geoip2_updater.py --force >> /var/log/geoip2_update.log 2>&1"

# Add to crontab if not already added
(crontab -l 2>/dev/null | grep -v "geoip2_updater.py"; echo "$CRON_JOB") | crontab -

echo "✅ Setup complete!"
echo ""
echo "📋 To use, add to .env:"
echo "GEOIP2_DB_PATH=/var/lib/geoip/GeoLite2-City.mmdb"
echo "GEOIP2_AUTO_UPDATE=true"
echo "RIPE_NCC_ENABLED=true"
echo ""
echo "🔍 Check status: python3 geoip2_updater.py --status"
