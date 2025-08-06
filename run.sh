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
    echo "Options:"
    echo "  test              Test Gmail connection"
    echo "  check [days]      Check for assignments (default: 7 days)"
    echo "  notion [days]     Check and sync to Notion"
    echo "  logs              Show recent logs"
    echo "  status            Show assignment summary"
    echo ""
    echo "Examples:"
    echo "  ./run.sh test"
    echo "  ./run.sh check 3"
    echo "  ./run.sh notion"
    echo "  ./run.sh logs"
}

# Parse command line arguments
case "$1" in
    "test")
        echo -e "${YELLOW}🧪 Testing connections...${NC}"
        $PYTHON_CMD run_fetcher.py --test
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
    "logs")
        echo -e "${YELLOW}📋 Recent logs:${NC}"
        if [ -f "moodle_fetcher.log" ]; then
            tail -20 moodle_fetcher.log
        else
            echo "No logs found yet"
        fi
        ;;
    "status")
        echo -e "${YELLOW}📊 Assignment Status:${NC}"
        if [ -f "assignments.json" ]; then
            echo "Total assignments found: $(cat assignments.json | grep -o '"title"' | wc -l)"
            echo ""
            echo "Recent assignments:"
            if [ -f "assignments.md" ]; then
                tail -10 assignments.md
            fi
        else
            echo "No assignments found yet. Run a check first."
        fi
        ;;
    *)
        show_usage
        ;;
esac
