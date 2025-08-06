#!/bin/bash

# Moodle Assignment Fetcher - Hosting Deployment Script
# This script sets up the application for production hosting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="moodle-fetcher"
USER_NAME="punisher"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Check if running as root for systemd setup
check_permissions() {
    if [[ $EUID -eq 0 ]] && [[ "$1" == "systemd" ]]; then
        log "Running as root for systemd setup"
        return 0
    elif [[ $EUID -ne 0 ]] && [[ "$1" == "app" ]]; then
        log "Running as regular user for application setup"
        return 0
    else
        log_error "Incorrect permissions for operation: $1"
        return 1
    fi
}

# Setup application (run as regular user)
setup_application() {
    log "🚀 Setting up Moodle Assignment Fetcher for hosting..."
    
    cd "$SCRIPT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment and install dependencies
    log "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Dependencies installed"
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warning ".env file created from example. Please configure your credentials!"
            log "Edit .env file with: nano .env"
        else
            log_error ".env.example file not found"
            return 1
        fi
    else
        log_success ".env file already exists"
    fi
    
    # Make scripts executable
    chmod +x daily_check.sh
    chmod +x deploy.sh
    log_success "Scripts made executable"
    
    # Create log directory if needed
    mkdir -p logs
    
    # Set proper permissions
    chmod 600 .env  # Secure credentials file
    chmod 755 daily_check.sh
    chmod 644 *.py
    
    log_success "File permissions set"
    
    # Test the configuration
    log "Testing configuration..."
    if source venv/bin/activate && python run_fetcher.py --test; then
        log_success "Configuration test passed"
    else
        log_error "Configuration test failed. Please check your .env file"
        return 1
    fi
}

# Setup systemd service (run as root)
setup_systemd() {
    log "🔧 Setting up systemd service..."
    
    # Copy service files
    cp "$SCRIPT_DIR/moodle-fetcher.service" /etc/systemd/system/
    cp "$SCRIPT_DIR/moodle-fetcher.timer" /etc/systemd/system/
    
    # Update paths in service file if needed
    sed -i "s|/home/punisher/Documents/automate|$SCRIPT_DIR|g" /etc/systemd/system/moodle-fetcher.service
    sed -i "s|User=punisher|User=$USER_NAME|g" /etc/systemd/system/moodle-fetcher.service
    sed -i "s|Group=punisher|Group=$USER_NAME|g" /etc/systemd/system/moodle-fetcher.service
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable and start timer
    systemctl enable moodle-fetcher.timer
    systemctl start moodle-fetcher.timer
    
    log_success "Systemd service configured and started"
    
    # Show status
    systemctl status moodle-fetcher.timer --no-pager
}

# Setup cron (alternative to systemd)
setup_cron() {
    log "⏰ Setting up cron jobs..."
    
    # Create cron job entries
    CRON_ENTRY_ACTIVE="0 8-22/2 * * * $SCRIPT_DIR/daily_check.sh"
    CRON_ENTRY_NIGHT="0 2 * * * $SCRIPT_DIR/daily_check.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "daily_check.sh" || true; echo "$CRON_ENTRY_ACTIVE"; echo "$CRON_ENTRY_NIGHT") | crontab -
    
    log_success "Cron jobs configured"
    log "Active hours: Every 2 hours from 8 AM to 10 PM"
    log "Night check: Once at 2 AM"
    
    # Show current crontab
    log "Current crontab:"
    crontab -l | grep -E "(daily_check|moodle)" || log "No moodle-related cron jobs found"
}

# Main deployment function
deploy() {
    local deployment_type="${1:-cron}"
    
    log "🎯 Starting deployment with type: $deployment_type"
    
    # Setup application components
    if ! setup_application; then
        log_error "Application setup failed"
        exit 1
    fi
    
    # Setup scheduling
    case "$deployment_type" in
        "systemd")
            if [[ $EUID -eq 0 ]]; then
                setup_systemd
            else
                log_error "Systemd setup requires root privileges"
                log "Run: sudo $0 systemd"
                exit 1
            fi
            ;;
        "cron")
            setup_cron
            ;;
        *)
            log_error "Unknown deployment type: $deployment_type"
            log "Usage: $0 [cron|systemd]"
            exit 1
            ;;
    esac
    
    # Final instructions
    log_success "🎉 Deployment completed successfully!"
    echo
    log "Next steps:"
    log "1. Configure your .env file with real credentials"
    log "2. Test manually: ./daily_check.sh"
    log "3. Monitor logs: tail -f cron_execution.log"
    echo
    log "Log files:"
    log "- cron_execution.log (execution logs)"
    log "- cron_errors.log (error logs)"
    log "- moodle_fetcher.log (application logs)"
    echo
    
    if [[ "$deployment_type" == "systemd" ]]; then
        log "Systemd commands:"
        log "- Check status: systemctl status moodle-fetcher.timer"
        log "- View logs: journalctl -u moodle-fetcher.service -f"
        log "- Stop timer: systemctl stop moodle-fetcher.timer"
    else
        log "Cron commands:"
        log "- View crontab: crontab -l"
        log "- Edit crontab: crontab -e"
        log "- Check cron logs: journalctl -u cronie -f"
    fi
}

# Show usage
show_usage() {
    echo "Moodle Assignment Fetcher - Deployment Script"
    echo
    echo "Usage: $0 [cron|systemd]"
    echo
    echo "Deployment types:"
    echo "  cron    - Use cron jobs for scheduling (default, runs as user)"
    echo "  systemd - Use systemd timer for scheduling (requires root)"
    echo
    echo "Examples:"
    echo "  $0                # Deploy with cron (default)"
    echo "  $0 cron          # Deploy with cron explicitly"
    echo "  sudo $0 systemd  # Deploy with systemd (as root)"
}

# Main script
main() {
    if [[ $# -eq 0 ]]; then
        deploy "cron"
    elif [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        show_usage
    else
        deploy "$1"
    fi
}

main "$@"
