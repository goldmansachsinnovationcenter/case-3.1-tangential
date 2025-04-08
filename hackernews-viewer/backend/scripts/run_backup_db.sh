
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKUP_SCRIPT="$SCRIPT_DIR/run_backup.py"
cd "$SCRIPT_DIR/../.."  # Changed to navigate to hackernews-viewer/ directory

mkdir -p "$(grep DATA_DIR .env | cut -d= -f2)/logs"

cd "backend" 
chmod +x "$BACKUP_SCRIPT"

echo "Starting database backup script in foreground mode."
echo "The script will run daily at midnight."

while true; do
    echo "Running database backup at $(date)"
    python3 "$BACKUP_SCRIPT"
    
    sleep_until=$(date -d "tomorrow 00:00:00" +%s)
    current=$(date +%s)
    sleep_seconds=$((sleep_until - current))
    
    echo "Next run scheduled at $(date -d "@$sleep_until"). Sleeping for $sleep_seconds seconds."
    sleep $sleep_seconds
done
