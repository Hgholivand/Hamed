#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/workspace"
DATE=$(date +%Y-%m-%d)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/workspace_$DATE.tar.gz" \
    /home/ubuntu/.openclaw/workspace/ \
    /home/ubuntu/market_fetcher.py \
    /home/ubuntu/.market_env 2>/dev/null
# Keep only last 14 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +14 -delete
echo "Backup done: workspace_$DATE.tar.gz"
