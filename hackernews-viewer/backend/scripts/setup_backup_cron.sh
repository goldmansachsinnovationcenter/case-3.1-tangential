
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.py"

chmod +x "$BACKUP_SCRIPT"

TEMP_CRONTAB=$(mktemp)

crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# HackerNews Viewer cron jobs" > "$TEMP_CRONTAB"

if ! grep -q "$BACKUP_SCRIPT" "$TEMP_CRONTAB"; then
    echo "# HackerNews Viewer - Daily database backup" >> "$TEMP_CRONTAB"
    echo "0 0 * * * cd $SCRIPT_DIR/.. && $BACKUP_SCRIPT >> $SCRIPT_DIR/../logs/backup_cron.log 2>&1" >> "$TEMP_CRONTAB"
    
    crontab "$TEMP_CRONTAB"
    echo "Backup cron job added successfully."
else
    echo "Backup cron job already exists."
fi

rm "$TEMP_CRONTAB"

mkdir -p "$SCRIPT_DIR/../logs"

echo "Backup cron job setup complete."
echo "The database will be backed up daily at midnight."
