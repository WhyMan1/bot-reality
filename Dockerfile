FROM python:3.11-slim

WORKDIR /app

# Create directory for GeoIP2 data
RUN mkdir -p /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl cron && apt-get clean

# Copy project files
COPY bot.py worker.py checker.py redis_queue.py progress_tracker.py analytics.py retry_logic.py cleanup_logs.sh ./
COPY geoip2_updater.py geoip2_integration.py ./

# Make scripts executable
RUN chmod +x cleanup_logs.sh
RUN chmod +x geoip2_updater.py

# Configure cron for daily log cleanup at 02:00
RUN echo "0 2 * * * /app/cleanup_logs.sh >> /tmp/cleanup.log 2>&1" | crontab -

# Configure cron for weekly GeoIP2 update on Sunday at 03:00
RUN echo "0 3 * * 0 cd /app && python geoip2_updater.py --force >> /tmp/geoip2_update.log 2>&1" | crontab -

# Download GeoIP2 database during image build
RUN cd /app && python geoip2_updater.py --force || echo "GeoIP2 download failed, will retry at runtime"

# Run cron in background and start the main application
CMD cron && python bot.py
