#!/bin/bash

# Log cleanup script for Docker container
# Runs daily at 2:00 via cron

LOG_DIR="/app"
MAX_LOG_SIZE="50M"
MAX_LOG_AGE=7  # days

echo "$(date): Starting log cleanup..."

# Remove old log files (older than 7 days)
find $LOG_DIR -name "*.log*" -type f -mtime +$MAX_LOG_AGE -delete 2>/dev/null

# Truncate large log files (> 50MB)
find $LOG_DIR -name "*.log*" -type f -size +$MAX_LOG_SIZE -exec truncate -s 0 {} \; 2>/dev/null

# Clean Docker system logs
if [ -w /var/log ]; then
    find /var/log -name "*.log" -type f -mtime +3 -delete 2>/dev/null
fi

# Clean temporary files
find /tmp -name "*.tmp" -type f -mtime +1 -delete 2>/dev/null
find /tmp -name "*.temp" -type f -mtime +1 -delete 2>/dev/null

# Clean pip cache if present
if [ -d "/root/.cache/pip" ]; then
    rm -rf /root/.cache/pip/* 2>/dev/null
fi

echo "$(date): Log cleanup completed"

# Show disk usage stats
df -h /app /tmp 2>/dev/null || true
