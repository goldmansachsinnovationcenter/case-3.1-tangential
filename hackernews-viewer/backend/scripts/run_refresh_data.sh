
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/refresh_data.py"
cd "$SCRIPT_DIR/../.."  # Changed to navigate to hackernews-viewer/ directory

mkdir -p "$(grep DATA_DIR .env | cut -d= -f2)/logs"

cd "backend" 
chmod +x "$REFRESH_SCRIPT"

echo "Starting data refresh script in foreground mode."
echo "The script will run every hour."

while true; do
    echo "Running data refresh at $(date)"
    python3 "$REFRESH_SCRIPT"
    
    sleep_until=$(date -d "$(date -d '+1 hour' '+%Y-%m-%d %H:00:00')" +%s)
    current=$(date +%s)
    sleep_seconds=$((sleep_until - current))
    
    echo "Next run scheduled at $(date -d "@$sleep_until"). Sleeping for $sleep_seconds seconds."
    sleep $sleep_seconds
done
