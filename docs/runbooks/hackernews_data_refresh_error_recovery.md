# HackerNews Data Refresh Error Recovery Runbook

## Overview

This runbook provides operational recovery steps for the "ERROR:app.services.hackernews:Error refreshing data" error in the HackerNews Viewer application. This error occurs when the automated data refresh process fails to update content from the HackerNews API.

## Error Identification

The error can be identified in the following ways:

1. In application logs, you will see:
   ```
   ERROR:app.services.hackernews:Error refreshing data
   ```

2. In the refresh.log file (if accessible), you may see:
   ```
   YYYY-MM-DD HH:MM:SS,SSS - app.services.hackernews - ERROR - Error refreshing data
   ```

3. The system status API endpoint may show the most recent refresh with a status of "error".

## Common Causes

The most common causes of this error are:

1. **Missing or inaccessible data directory**: The DATA_DIR environment variable points to a location that doesn't exist or is not accessible.
2. **Database access issues**: The database file is missing, corrupted, or has permission issues.
3. **Network connectivity problems**: The application cannot connect to the HackerNews API.
4. **Insufficient disk space**: The system has run out of disk space for storing logs or database files.

## Recovery Steps

### 1. Verify Environment Configuration

1. Check the .env file location and content:
   ```bash
   cat hackernews-viewer/.env
   ```

2. Verify that the DATA_DIR path exists and is accessible:
   ```bash
   # Check if the directory exists
   ls -la $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)
   
   # If it doesn't exist, create it
   mkdir -p $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)
   mkdir -p $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/logs
   mkdir -p $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/backups
   ```

3. Ensure proper permissions on the data directory:
   ```bash
   chmod -R 755 $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)
   ```

### 2. Verify Database Status

1. Check if the database file exists:
   ```bash
   ls -la $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/hackernews.db
   ```

2. If the database doesn't exist, it will be created automatically when the refresh process runs successfully.

3. If the database exists but might be corrupted, you can restore from a backup (if available):
   ```bash
   # List available backups
   ls -la $(grep BACKUP_DIR hackernews-viewer/.env | cut -d= -f2)
   
   # Copy the most recent backup to replace the current database
   cp $(grep BACKUP_DIR hackernews-viewer/.env | cut -d= -f2)/[BACKUP_FILENAME] $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/hackernews.db
   ```

### 3. Verify Network Connectivity

1. Check connectivity to the HackerNews API:
   ```bash
   curl -I https://hacker-news.firebaseio.com/v0/topstories.json
   ```

2. If there are network issues, verify your network configuration and proxy settings if applicable.

### 4. Check Disk Space

1. Verify available disk space:
   ```bash
   df -h
   ```

2. If disk space is low, clean up unnecessary files or expand storage capacity.

### 5. Restart the Data Refresh Process

1. Run the refresh script manually to test:
   ```bash
   cd hackernews-viewer/backend
   python scripts/refresh_data.py
   ```

2. If the manual run is successful, restart the scheduled refresh process:
   ```bash
   # Kill any existing refresh process
   pkill -f run_refresh_data.sh
   
   # Start the refresh process in the background
   cd hackernews-viewer/backend/scripts
   nohup ./run_refresh_data.sh > /dev/null 2>&1 &
   ```

### 6. Verify Recovery

1. Check the refresh logs for successful execution:
   ```bash
   tail -f $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/logs/refresh.log
   ```

2. Check the system status API endpoint to confirm the refresh status has changed to "success".

3. Verify that new HackerNews content is being displayed in the frontend.

## Preventive Measures

To prevent this error from recurring:

1. Set up monitoring for the refresh process to detect failures early.
2. Configure alerts for disk space usage before it becomes critical.
3. Implement regular database backups (already part of the system).
4. Consider setting up a health check endpoint that verifies the refresh process is running correctly.

## Contact Information

If you are unable to resolve the issue using this runbook, contact the application support team or the developer responsible for the HackerNews Viewer application.
