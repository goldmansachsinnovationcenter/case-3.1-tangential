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

## Criticality Levels and Response Expectations

The HackerNews data refresh errors are categorized into the following criticality levels:

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P0 | Critical - System completely non-functional, data integrity at risk | Immediate (< 1 hour) | Database corruption, Database access errors |
| P1 | High - Major functionality impaired, but system partially operational | Within 4 hours | DATA_DIR inaccessible, Disk space critically low, HackerNews API unavailable |
| P2 | Medium - Limited functionality affected, workarounds available | Within 24 hours | Error fetching top stories, Multiple item fetch failures |
| P3 | Low - Minor issues with minimal impact on functionality | Within 1 week | Individual item fetch errors, Invalid item types |

## Common Causes

The most common causes of this error are:

1. **Missing or inaccessible data directory** (P1): The DATA_DIR environment variable points to a location that doesn't exist or is not accessible.
2. **Database access issues** (P0): The database file is missing, corrupted, or has permission issues.
3. **Network connectivity problems** (P1): The application cannot connect to the HackerNews API.
4. **Insufficient disk space** (P1): The system has run out of disk space for storing logs or database files.

## Recovery Steps

### 1. Verify Environment Configuration (P1)

**Error Message:** `P1: DATA_DIR at {path} does not exist`, `P1: DATA_DIR at {path} is not readable`, or `P1: DATA_DIR at {path} is not writable`

**Resolution Steps:**
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

### 2. Verify Database Status (P0)

**Error Message:** `P0: Database file at {path} does not exist`, `P0: Database corruption detected in {path}`, or `P0: Database access error`

**Resolution Steps:**
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

### 3. Verify Network Connectivity (P1)

**Error Message:** `P1: HackerNews API is unavailable`

**Resolution Steps:**
1. Check connectivity to the HackerNews API:
   ```bash
   curl -I https://hacker-news.firebaseio.com/v0/topstories.json
   ```

2. If there are network issues, verify your network configuration and proxy settings if applicable.

### 4. Check Disk Space (P1)

**Error Message:** `P1: Disk space critically low: {percentage}% free, {size} GB`

**Resolution Steps:**
1. Verify available disk space:
   ```bash
   df -h
   ```

2. If disk space is low, clean up unnecessary files or expand storage capacity.

### 5. Handle Item Fetch Errors (P2/P3)

**Error Message:** `P2: Error fetching top stories`, `P3: Error fetching item {id}`, or `P3: Error fetching user {username}`

**Resolution Steps:**
1. These errors are often transient and may resolve on their own. Wait for the next scheduled refresh or retry manually:
   ```bash
   cd hackernews-viewer/backend
   python scripts/refresh_data.py
   ```

2. If errors persist, check the HackerNews API status and your network connectivity.

### 6. Restart the Data Refresh Process

**Resolution Steps:**
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

### 7. Verify Recovery

**Resolution Steps:**
1. Check the refresh logs for successful execution:
   ```bash
   tail -f $(grep DATA_DIR hackernews-viewer/.env | cut -d= -f2)/logs/refresh.log
   ```

2. Check the system status API endpoint to confirm the refresh status has changed to "success".

3. Verify that new HackerNews content is being displayed in the frontend.

## Preventive Measures

To prevent these errors from recurring:

1. Set up monitoring for the refresh process to detect failures early:
   - Configure alerts for P0 and P1 issues to notify on-call personnel immediately
   - Set up daily reports for P2 and P3 issues

2. Configure alerts for disk space usage before it becomes critical (P1):
   - Set warning thresholds at 20% free space
   - Set critical thresholds at 10% free space

3. Implement regular database backups to prevent data loss from corruption (P0):
   - Daily full backups (already part of the system)
   - Consider more frequent incremental backups for critical deployments

4. Consider setting up a health check endpoint that verifies the refresh process is running correctly:
   - Monitor for consecutive refresh failures
   - Implement automatic recovery procedures for common issues

## Contact Information

If you are unable to resolve the issue using this runbook, contact the application support team or the developer responsible for the HackerNews Viewer application.
