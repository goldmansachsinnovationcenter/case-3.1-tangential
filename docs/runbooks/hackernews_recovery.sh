

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
    print_header "Verifying Environment Configuration"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Environment file not found at $ENV_FILE"
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
        print_warning "DATA_DIR does not exist. Creating it now..."
        mkdir -p "$DATA_DIR"
        mkdir -p "$DATA_DIR/logs"
        mkdir -p "$DATA_DIR/backups"
        print_success "Created DATA_DIR and subdirectories."
    else
        print_success "DATA_DIR exists."
    fi
    
    chmod -R 755 "$DATA_DIR"
    print_success "Set permissions on DATA_DIR."
}

verify_database() {
    print_header "Verifying Database Status"
    
    DB_FILE="$DATA_DIR/hackernews.db"
    if [[ ! -f "$DB_FILE" ]]; then
        print_warning "Database file does not exist at $DB_FILE"
        print_warning "It will be created when the refresh process runs successfully."
    else
        print_success "Database file exists at $DB_FILE"
        
        if sqlite3 "$DB_FILE" "SELECT 1;" &>/dev/null; then
            print_success "Database is accessible and not corrupted."
        else
            print_warning "Database might be corrupted."
            
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
    print_header "Verifying Network Connectivity"
    
    if curl -s -I "https://hacker-news.firebaseio.com/v0/topstories.json" &>/dev/null; then
        print_success "Successfully connected to HackerNews API."
    else
        print_error "Failed to connect to HackerNews API."
        print_warning "Please check your network configuration and proxy settings."
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_disk_space() {
    print_header "Checking Disk Space"
    
    DISK_SPACE=$(df -h "$DATA_DIR" | awk 'NR==2 {print $4}')
    DISK_USAGE=$(df -h "$DATA_DIR" | awk 'NR==2 {print $5}')
    
    echo "Available disk space: $DISK_SPACE"
    echo "Disk usage: $DISK_USAGE"
    
    USAGE_PERCENT=${DISK_USAGE%\%}
    
    if [[ $USAGE_PERCENT -gt 90 ]]; then
        print_warning "Disk usage is very high (>90%). This might cause issues."
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
    
    cd "$APP_ROOT/hackernews-viewer/backend"
    
    print_warning "Running refresh script manually to test..."
    if python scripts/refresh_data.py; then
        print_success "Manual refresh completed successfully."
    else
        print_error "Manual refresh failed."
        read -p "Continue with restart anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_warning "Killing any existing refresh processes..."
    pkill -f run_refresh_data.sh || true
    
    print_warning "Starting refresh process in the background..."
    cd scripts
    nohup ./run_refresh_data.sh > /dev/null 2>&1 &
    
    print_success "Refresh process restarted in the background."
}

verify_recovery() {
    print_header "Verifying Recovery"
    
    print_warning "Checking refresh logs (press Ctrl+C to stop)..."
    echo "Waiting for log entries..."
    
    sleep 5
    
    LOG_FILE="$DATA_DIR/logs/refresh.log"
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 10 "$LOG_FILE"
        
        if grep -q "ERROR:app.services.hackernews:Error refreshing data" "$LOG_FILE"; then
            print_error "Error still present in logs. Recovery might not be complete."
        else
            print_success "No errors found in recent logs."
        fi
    else
        print_warning "Log file not found at $LOG_FILE"
    fi
    
    print_warning "Please verify that new HackerNews content is being displayed in the frontend."
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
    restart_refresh_process
    verify_recovery
    
    print_header "Recovery Process Complete"
    echo "The HackerNews data refresh process has been recovered."
    echo "If you continue to experience issues, please refer to the full runbook at:"
    echo "$SCRIPT_DIR/hackernews_data_refresh_error_recovery.md"
}

main
