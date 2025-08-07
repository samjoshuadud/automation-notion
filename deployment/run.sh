#!/bin/bash

# Quick start script for Moodle Assignment Fetcher
# This script handles virtual environment activation automatically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv venv && source venv/bin/activate.fish && pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your Gmail credentials"
    exit 1
fi

# Use virtual environment Python
PYTHON_CMD="venv/bin/python"

# Function to show usage
show_usage() {
    echo "Usage: ./run.sh [OPTIONS]"
    echo ""
    echo "Basic Commands:"
    echo "  test              Test all connections (Gmail, Notion, Todoist)"
    echo "  check [days]      Check for assignments (default: 7 days)"
    echo "  notion [days]     Check and sync to Notion database"
    echo "  logs              Show recent logs"
    echo "  status            Show detailed assignment status report"
    echo ""
    echo "Advanced Commands:"
    echo "  verbose [cmd]     Run any command with detailed verbose logging"
    echo "  debug [cmd]       Run any command with maximum debug output"
    echo "  duplicates        Show duplicate detection analysis"
    echo "  archive-stats     Show archive statistics"
    echo "  delete-all        Delete all assignments (and from Todoist) - DEBUG ONLY"
    echo ""
    echo "Examples:"
    echo "  ./run.sh test                    # Test connections"
    echo "  ./run.sh check 3                # Check last 3 days"
    echo "  ./run.sh notion                 # Full Notion sync"
    echo "  ./run.sh verbose check          # Verbose assignment check"
    echo "  ./run.sh debug notion 14        # Debug mode with 14 days + Notion"
    echo "  ./run.sh status                 # Detailed status report"
    echo "  ./run.sh duplicates             # Check for duplicate assignments"
    echo "  ./run.sh delete-all             # Delete all assignments (DEBUG)"
    echo "  ./run.sh logs                   # View recent activity"
}

# Parse command line arguments
case "$1" in
    "test")
        echo -e "${YELLOW}🧪 Testing connections...${NC}"
        $PYTHON_CMD run_fetcher.py --test --verbose
        ;;
    "check")
        DAYS=${2:-7}
        echo -e "${YELLOW}📧 Checking for assignments from last $DAYS days...${NC}"
        $PYTHON_CMD run_fetcher.py --days $DAYS --verbose
        ;;
    "notion")
        DAYS=${2:-7}
        echo -e "${YELLOW}📧 Checking assignments and syncing to Notion...${NC}"
        $PYTHON_CMD run_fetcher.py --days $DAYS --notion --verbose
        ;;
    "verbose")
        shift  # Remove 'verbose' from arguments
        case "$1" in
            "check")
                DAYS=${2:-7}
                echo -e "${GREEN}� VERBOSE MODE: Checking assignments with detailed logging...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --verbose
                ;;
            "notion")
                DAYS=${2:-7}
                echo -e "${GREEN}🔍 VERBOSE MODE: Notion sync with detailed logging...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --notion --verbose
                ;;
            "test")
                echo -e "${GREEN}🔍 VERBOSE MODE: Testing connections with detailed output...${NC}"
                $PYTHON_CMD run_fetcher.py --test --notion --todoist --verbose
                ;;
            *)
                echo -e "${RED}❌ Invalid verbose command. Use: verbose [check|notion|test]${NC}"
                show_usage
                exit 1
                ;;
        esac
        ;;
    "debug")
        shift  # Remove 'debug' from arguments
        case "$1" in
            "check")
                DAYS=${2:-7}
                echo -e "${RED}� DEBUG MODE: Maximum detail logging enabled...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --debug
                ;;
            "notion")
                DAYS=${2:-7}
                echo -e "${RED}🐛 DEBUG MODE: Notion sync with maximum detail...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --notion --debug
                ;;
            "test")
                echo -e "${RED}🐛 DEBUG MODE: Testing with maximum detail...${NC}"
                $PYTHON_CMD run_fetcher.py --test --notion --todoist --debug
                ;;
            *)
                echo -e "${RED}❌ Invalid debug command. Use: debug [check|notion|test]${NC}"
                show_usage
                exit 1
                ;;
        esac
        ;;
    "status")
        echo -e "${YELLOW}📊 Detailed Assignment Status Report...${NC}"
        $PYTHON_CMD run_fetcher.py --status-report
        ;;
    "duplicates")
        echo -e "${YELLOW}🔍 Duplicate Detection Analysis...${NC}"
        $PYTHON_CMD run_fetcher.py --show-duplicates
        ;;
    "archive-stats")
        echo -e "${YELLOW}📊 Archive Statistics...${NC}"
        $PYTHON_CMD run_fetcher.py --archive-stats
        ;;
    "delete-all")
        echo -e "${RED}🗑️ DANGER: Deleting all assignments from database, Todoist, and Notion...${NC}"
        echo -e "${YELLOW}⚠️ This will NOT delete your emails - only synced assignments${NC}"
        echo -e "${YELLOW}Press Ctrl+C in the next 5 seconds to cancel...${NC}"
        sleep 5
        echo -e "${RED}🗑️ Proceeding with deletion...${NC}"
        $PYTHON_CMD run_fetcher.py --delete-all-assignments --verbose
        ;;
    "logs")
        echo -e "${YELLOW}📋 Recent logs:${NC}"
        if [ -f "logs/moodle_fetcher.log" ]; then
            tail -30 logs/moodle_fetcher.log
        elif [ -f "moodle_fetcher.log" ]; then
            tail -30 moodle_fetcher.log
        else
            echo "No logs found yet"
        fi
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac
