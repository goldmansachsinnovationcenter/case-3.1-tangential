

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/../.." &> /dev/null && pwd)"
ENV_FILE="$APP_ROOT/hackernews-viewer/.env"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BOLD}${1}${NC}"
    echo "========================================"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}! ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_criticality() {
    local level=$1
    local message=$2
    
    case $level in
        P0)
            echo -e "${RED}[P0] CRITICAL: ${message}${NC}"
            ;;
        P1)
            echo -e "${RED}[P1] HIGH: ${message}${NC}"
            ;;
        P2)
            echo -e "${YELLOW}[P2] MEDIUM: ${message}${NC}"
            ;;
        P3)
            echo -e "${YELLOW}[P3] LOW: ${message}${NC}"
            ;;
        *)
            echo -e "${message}"
            ;;
    esac
}

check_privileges() {
    print_header "Checking Privileges"
    if [[ $EUID -ne 0 ]]; then
        print_warning "This script is not being run as root. Some operations might fail."
        print_warning "Consider running with sudo if you encounter permission issues."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Script is running with root privileges."
    fi
}

verify_env_config() {
    print_header "Verifying Environment Configuration (P1)"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_criticality "P1" "Environment file not found at $ENV_FILE"
        exit 1
    else
        print_success "Environment file found at $ENV_FILE"
    fi
    
    DATA_DIR=$(grep DATA_DIR "$ENV_FILE" | cut -d= -f2)
    DATA_DIR=${DATA_DIR//\$\{DATA_DIR\}/$(grep DATA_DIR "$ENV_FILE" | cut -d= -f2)}
    
    BACKUP_DIR=$(grep BACKUP_DIR "$ENV_FILE" | cut -d= -f2)
    BACKUP_DIR=${BACKUP_DIR//\$\{DATA_DIR\}/$(grep DATA_DIR "$ENV_FILE" | cut -d= -f2)}
    
    echo "DATA_DIR: $DATA_DIR"
    echo "BACKUP_DIR: $BACKUP_DIR"
    
    if [[ ! -d "$DATA_DIR" ]]; then
        print_criticality "P1" "DATA_DIR does not exist. Creating it now..."
        mkdir -p "$DATA_DIR"
        mkdir -p "$DATA_DIR/logs"
        mkdir -p "$DATA_DIR/backups"
        print_success "Created DATA_DIR and subdirectories."
    else
        print_success "DATA_DIR exists."
    fi
    
    if [[ ! -r "$DATA_DIR" ]]; then
        print_criticality "P1" "DATA_DIR at $DATA_DIR is not readable"
        chmod -R 755 "$DATA_DIR"
    fi
    
    if [[ ! -w "$DATA_DIR" ]]; then
        print_criticality "P1" "DATA_DIR at $DATA_DIR is not writable"
        chmod -R 755 "$DATA_DIR"
    else
        chmod -R 755 "$DATA_DIR"
        print_success "Set permissions on DATA_DIR."
    fi
}

verify_database() {
    print_header "Verifying Database Status (P0)"
    
    DB_FILE="$DATA_DIR/hackernews.db"
    if [[ ! -f "$DB_FILE" ]]; then
        print_criticality "P0" "Database file at $DB_FILE does not exist"
        print_warning "It will be created when the refresh process runs successfully."
    else
        print_success "Database file exists at $DB_FILE"
        
        if sqlite3 "$DB_FILE" "SELECT 1;" &>/dev/null; then
            print_success "Database is accessible and not corrupted."
        else
            print_criticality "P0" "Database corruption detected in $DB_FILE"
            
            BACKUPS=$(find "$BACKUP_DIR" -name "*.db" -type f | sort -r)
            if [[ -n "$BACKUPS" ]]; then
                print_warning "Found backups. Latest backup: $(echo "$BACKUPS" | head -n1)"
                read -p "Restore from latest backup? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    LATEST_BACKUP=$(echo "$BACKUPS" | head -n1)
                    cp "$LATEST_BACKUP" "$DB_FILE"
                    print_success "Restored database from backup: $LATEST_BACKUP"
                fi
            else
                print_warning "No backups found. A new database will be created when the refresh process runs."
            fi
        fi
    fi
}

verify_network() {
    print_header "Verifying Network Connectivity (P1)"
    
    if curl -s -I "https://hacker-news.firebaseio.com/v0/topstories.json" &>/dev/null; then
        print_success "Successfully connected to HackerNews API."
    else
        print_criticality "P1" "HackerNews API is unavailable"
        print_warning "Please check your network configuration and proxy settings."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_disk_space() {
    print_header "Checking Disk Space (P1)"
    
    DISK_SPACE=$(df -h "$DATA_DIR" | awk 'NR==2 {print $4}')
    DISK_USAGE=$(df -h "$DATA_DIR" | awk 'NR==2 {print $5}')
    
    echo "Available disk space: $DISK_SPACE"
    echo "Disk usage: $DISK_USAGE"
    
    USAGE_PERCENT=${DISK_USAGE%\%}
    FREE_PERCENT=$((100 - USAGE_PERCENT))
    
    if [[ $USAGE_PERCENT -gt 90 ]]; then
        print_criticality "P1" "Disk space critically low: ${FREE_PERCENT}% free, ${DISK_SPACE}"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    elif [[ $USAGE_PERCENT -gt 80 ]]; then
        print_warning "Disk usage is high (>80%). Consider freeing up space."
    else
        print_success "Sufficient disk space available."
    fi
}

restart_refresh_process() {
    print_header "Restarting Data Refresh Process"
    
    BACKEND_DIR="$APP_ROOT/hackernews-viewer/backend"
    if [[ ! -d "$BACKEND_DIR" ]]; then
        print_criticality "P1" "Backend directory not found at $BACKEND_DIR"
        print_warning "This script may be running in a test environment."
        print_warning "Skipping refresh process restart."
        return
    fi
    
    cd "$BACKEND_DIR"
    
    print_warning "Running refresh script manually to test..."
    if [[ -f "scripts/refresh_data.py" ]]; then
        if python scripts/refresh_data.py; then
            print_success "Manual refresh completed successfully."
        else
            print_criticality "P1" "Error refreshing data"
            read -p "Continue with restart anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_criticality "P1" "Refresh script not found at scripts/refresh_data.py"
        print_warning "Skipping manual refresh test."
    fi
    
    print_warning "Killing any existing refresh processes..."
    pkill -f run_refresh_data.sh || true
    
    if [[ -d "scripts" && -f "scripts/run_refresh_data.sh" ]]; then
        print_warning "Starting refresh process in the background..."
        cd scripts
        nohup ./run_refresh_data.sh > /dev/null 2>&1 &
        print_success "Refresh process restarted in the background."
    else
        print_criticality "P1" "Refresh script not found at scripts/run_refresh_data.sh"
        print_warning "Skipping refresh process restart."
    fi
}

verify_recovery() {
    print_header "Verifying Recovery"
    
    LOG_FILE="$DATA_DIR/logs/refresh.log"
    if [[ ! -d "$DATA_DIR/logs" ]]; then
        print_warning "Log directory not found at $DATA_DIR/logs"
        print_warning "Creating log directory..."
        mkdir -p "$DATA_DIR/logs"
        print_success "Created log directory."
        print_warning "A new log file will be created when the refresh process runs."
        return
    fi
    
    if [[ ! -f "$LOG_FILE" ]]; then
        print_warning "Log file not found at $LOG_FILE"
        print_warning "This may be a new installation or the logs may have been cleared."
        print_warning "A new log file will be created when the refresh process runs."
        return
    fi
    
    print_warning "Checking refresh logs (press Ctrl+C to stop)..."
    echo "Waiting for log entries..."
    
    sleep 5
    
    tail -n 10 "$LOG_FILE"
    
    if grep -q "ERROR:app.services.hackernews:P0:" "$LOG_FILE"; then
        print_criticality "P0" "Critical errors still present in logs. Recovery might not be complete."
    elif grep -q "ERROR:app.services.hackernews:P1:" "$LOG_FILE"; then
        print_criticality "P1" "High severity errors still present in logs. Recovery might not be complete."
    elif grep -q "ERROR:app.services.hackernews:P2:" "$LOG_FILE"; then
        print_criticality "P2" "Medium severity errors still present in logs. Recovery might not be complete."
    elif grep -q "ERROR:app.services.hackernews:P3:" "$LOG_FILE"; then
        print_criticality "P3" "Low severity errors still present in logs. Recovery might not be complete."
    elif grep -q "ERROR:app.services.hackernews:Error refreshing data" "$LOG_FILE"; then
        print_error "Error still present in logs (old format). Recovery might not be complete."
    else
        print_success "No errors found in recent logs."
    fi
    
    print_warning "Please verify that new HackerNews content is being displayed in the frontend."
}

handle_item_fetch_errors() {
    print_header "Handling Item Fetch Errors (P2/P3)"
    
    LOG_FILE="$DATA_DIR/logs/refresh.log"
    if [[ -f "$LOG_FILE" ]]; then
        if grep -q "ERROR:app.services.hackernews:P2: Error fetching top stories" "$LOG_FILE"; then
            print_criticality "P2" "Error fetching top stories detected"
            print_warning "This error may be transient. Attempting to refresh data again..."
            cd "$APP_ROOT/hackernews-viewer/backend"
            python scripts/refresh_data.py
        fi
        
        if grep -q "ERROR:app.services.hackernews:P3: Error fetching item" "$LOG_FILE" || \
           grep -q "ERROR:app.services.hackernews:P3: Error fetching user" "$LOG_FILE"; then
            print_criticality "P3" "Error fetching individual items or users detected"
            print_warning "These errors are usually minor and may resolve on their own."
            print_warning "If they persist, check network connectivity and HackerNews API status."
        fi
    else
        print_warning "Log file not found at $LOG_FILE"
    fi
}

main() {
    echo -e "${BOLD}HackerNews Data Refresh Error Recovery Script${NC}"
    echo "This script automates the recovery steps from the HackerNews data refresh error runbook."
    echo
    
    check_privileges
    verify_env_config
    verify_database
    verify_network
    check_disk_space
    handle_item_fetch_errors
    restart_refresh_process
    verify_recovery
    
    print_header "Recovery Process Complete"
    echo "The HackerNews data refresh process has been recovered."
    echo "If you continue to experience issues, please refer to the full runbook at:"
    echo "$SCRIPT_DIR/hackernews_data_refresh_error_recovery.md"
}

main
