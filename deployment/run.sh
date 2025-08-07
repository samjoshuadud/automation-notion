#!/bin/bash

# Quick start script for Moodle Assignment Fetcher
# This script handles virtual environment activation automatically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

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
    echo "  todoist [days]    Check and sync to Todoist tasks"
    echo "  both [days]       Check and sync to both Notion and Todoist"
    echo "  logs              Show recent logs"
    echo "  status            Show detailed assignment status report"
    echo ""
    echo "Advanced Commands:"
    echo "  verbose [cmd]     Run any command with detailed verbose logging"
    echo "  debug [cmd]       Run any command with maximum debug output"
    echo "  duplicates        Show duplicate detection analysis"
    echo "  archive-stats     Show archive statistics"
    echo "  delete-all [target] [--include-local]   Delete assignments - target: notion, todoist, both (default: both)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh test                    # Test connections"
    echo "  ./run.sh check 3                # Check last 3 days"
    echo "  ./run.sh notion                 # Full Notion sync"
    echo "  ./run.sh todoist                # Full Todoist sync"
    echo "  ./run.sh both                   # Sync to both Notion and Todoist"
    echo "  ./run.sh verbose check          # Verbose assignment check"
    echo "  ./run.sh debug both 14          # Debug mode with 14 days + both platforms"
    echo "  ./run.sh status                 # Detailed status report"
    echo "  ./run.sh duplicates             # Check for duplicate assignments"
    echo "  ./run.sh delete-all             # Delete all assignments (DEBUG)"
    echo "  ./run.sh delete-all notion      # Delete only from Notion"
    echo "  ./run.sh delete-all todoist     # Delete only from Todoist"
    echo "  ./run.sh delete-all both --include-local  # Delete from both + local database"
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
    "todoist")
        DAYS=${2:-7}
        echo -e "${YELLOW}📧 Checking assignments and syncing to Todoist...${NC}"
        $PYTHON_CMD run_fetcher.py --days $DAYS --todoist --verbose
        ;;
    "both")
        DAYS=${2:-7}
        echo -e "${YELLOW}📧 Checking assignments and syncing to both Notion and Todoist...${NC}"
        $PYTHON_CMD run_fetcher.py --days $DAYS --notion --todoist --verbose
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
            "todoist")
                DAYS=${2:-7}
                echo -e "${GREEN}🔍 VERBOSE MODE: Todoist sync with detailed logging...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --todoist --verbose
                ;;
            "both")
                DAYS=${2:-7}
                echo -e "${GREEN}🔍 VERBOSE MODE: Both platforms sync with detailed logging...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --notion --todoist --verbose
                ;;
            "test")
                echo -e "${GREEN}🔍 VERBOSE MODE: Testing connections with detailed output...${NC}"
                $PYTHON_CMD run_fetcher.py --test --notion --todoist --verbose
                ;;
            *)
                echo -e "${RED}❌ Invalid verbose command. Use: verbose [check|notion|todoist|both|test]${NC}"
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
            "todoist")
                DAYS=${2:-7}
                echo -e "${RED}🐛 DEBUG MODE: Todoist sync with maximum detail...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --todoist --debug
                ;;
            "both")
                DAYS=${2:-7}
                echo -e "${RED}🐛 DEBUG MODE: Both platforms sync with maximum detail...${NC}"
                $PYTHON_CMD run_fetcher.py --days $DAYS --notion --todoist --debug
                ;;
            "test")
                echo -e "${RED}🐛 DEBUG MODE: Testing with maximum detail...${NC}"
                $PYTHON_CMD run_fetcher.py --test --notion --todoist --debug
                ;;
            *)
                echo -e "${RED}❌ Invalid debug command. Use: debug [check|notion|todoist|both|test]${NC}"
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
        TARGET=${2:-both}
        INCLUDE_LOCAL=""
        
        # Check if --include-local flag is provided (can be 2nd or 3rd argument)
        if [[ "$2" == "--include-local" ]] || [[ "$3" == "--include-local" ]]; then
            INCLUDE_LOCAL="--include-local"
        fi
        
        # If 2nd arg is --include-local, use default target
        if [[ "$2" == "--include-local" ]]; then
            TARGET="both"
        fi
        
        case "$TARGET" in
            "notion"|"todoist"|"both")
                LOCAL_TEXT=""
                if [[ -n "$INCLUDE_LOCAL" ]]; then
                    LOCAL_TEXT=" + local database"
                fi
                echo -e "${RED}🗑️ DANGER: Deleting all assignments from $TARGET$LOCAL_TEXT...${NC}"
                echo -e "${YELLOW}⚠️ This will NOT delete your emails - only synced assignments${NC}"
                echo -e "${YELLOW}Press Ctrl+C in the next 5 seconds to cancel...${NC}"
                sleep 5
                echo -e "${RED}🗑️ Proceeding with $TARGET deletion$LOCAL_TEXT...${NC}"
                $PYTHON_CMD run_fetcher.py --delete-all-assignments --delete-from $TARGET $INCLUDE_LOCAL --verbose
                ;;
            *)
                echo -e "${RED}❌ Invalid target: $TARGET${NC}"
                echo "Valid targets: notion, todoist, both"
                echo "Usage: ./run.sh delete-all [notion|todoist|both] [--include-local]"
                exit 1
                ;;
        esac
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
