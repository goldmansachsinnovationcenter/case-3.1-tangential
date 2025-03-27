
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/refresh_data.py"

chmod +x "$REFRESH_SCRIPT"

TEMP_CRONTAB=$(mktemp)

crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# HackerNews Viewer cron jobs" > "$TEMP_CRONTAB"

if ! grep -q "$REFRESH_SCRIPT" "$TEMP_CRONTAB"; then
    echo "# HackerNews Viewer - Hourly data refresh" >> "$TEMP_CRONTAB"
    echo "0 * * * * cd $SCRIPT_DIR/.. && $REFRESH_SCRIPT >> $SCRIPT_DIR/../logs/cron.log 2>&1" >> "$TEMP_CRONTAB"
    
    crontab "$TEMP_CRONTAB"
    echo "Cron job added successfully."
else
    echo "Cron job already exists."
fi

rm "$TEMP_CRONTAB"

mkdir -p "$SCRIPT_DIR/../logs"

echo "Cron job setup complete."
echo "The data will be refreshed hourly at minute 0."
