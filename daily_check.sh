#!/bin/bash

# Moodle Assignment Fetcher - Production Cron Script
# Optimized for hosting environments with proper logging and error handling
# 
# Recommended crontab entries:
# Every 2 hours during active time (8 AM - 10 PM):
# 0 8-22/2 * * * /home/punisher/Documents/automate/daily_check.sh
#
# Once at night (2 AM):
# 0 2 * * * /home/punisher/Documents/automate/daily_check.sh

set -euo pipefail  # Exit on any error, undefined variable, or pipe failure

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_CMD="$VENV_DIR/bin/python"
LOG_FILE="$SCRIPT_DIR/cron_execution.log"
ERROR_LOG="$SCRIPT_DIR/cron_errors.log"
LOCK_FILE="$SCRIPT_DIR/.moodle_fetcher.lock"
MAX_RUNTIME=300  # 5 minutes max runtime

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [CRON] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" | tee -a "$ERROR_LOG" >&2
}

# Function to cleanup on exit
cleanup() {
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log "Lock file removed"
    fi
}
trap cleanup EXIT

# Check if already running (prevent overlapping executions)
if [[ -f "$LOCK_FILE" ]]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [[ -n "$LOCK_PID" ]] && kill -0 "$LOCK_PID" 2>/dev/null; then
        log_error "Another instance is already running (PID: $LOCK_PID). Exiting."
        exit 1
    else
        log "Stale lock file found. Removing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
log "Starting Moodle Assignment Fetcher (PID: $$)"

# Change to project directory
cd "$SCRIPT_DIR" || {
    log_error "Failed to change to script directory: $SCRIPT_DIR"
    exit 1
}

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    log_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Check if Python executable exists
if [[ ! -x "$PYTHON_CMD" ]]; then
    log_error "Python executable not found at $PYTHON_CMD"
    exit 1
fi

# Check if main script exists
if [[ ! -f "run_fetcher.py" ]]; then
    log_error "Main script run_fetcher.py not found"
    exit 1
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    log_error "Configuration file .env not found"
    exit 1
fi

# Determine run type based on time of day
CURRENT_HOUR=$(date +%H)
if (( CURRENT_HOUR >= 8 && CURRENT_HOUR <= 22 )); then
    RUN_TYPE="active"
    DAYS_BACK=7
    log "Active hours detected - checking last $DAYS_BACK days"
else
    RUN_TYPE="night"
    DAYS_BACK=7
    log "Night hours detected - checking last $DAYS_BACK days"
fi

# Run the fetcher with timeout
log "Executing: $PYTHON_CMD run_fetcher.py --days $DAYS_BACK --notion --verbose"

if timeout $MAX_RUNTIME "$PYTHON_CMD" run_fetcher.py --days $DAYS_BACK --notion --verbose >> "$LOG_FILE" 2>> "$ERROR_LOG"; then
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 0 ]]; then
        log "✅ Moodle Assignment Fetcher completed successfully"
    else
        log_error "❌ Moodle Assignment Fetcher completed with exit code: $EXIT_CODE"
    fi
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 124 ]]; then
        log_error "❌ Moodle Assignment Fetcher timed out after $MAX_RUNTIME seconds"
    else
        log_error "❌ Moodle Assignment Fetcher failed with exit code: $EXIT_CODE"
    fi
fi

# Check log file sizes and rotate if needed
MAX_LOG_SIZE=10485760  # 10MB in bytes

rotate_log() {
    local log_file="$1"
    local max_size="$2"
    
    if [[ -f "$log_file" ]] && [[ $(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo 0) -gt $max_size ]]; then
        mv "$log_file" "${log_file}.old"
        log "Rotated log file: $log_file"
    fi
}

rotate_log "$LOG_FILE" $MAX_LOG_SIZE
rotate_log "$ERROR_LOG" $MAX_LOG_SIZE
rotate_log "$SCRIPT_DIR/moodle_fetcher.log" $MAX_LOG_SIZE

log "Cron execution finished"
exit $EXIT_CODE
