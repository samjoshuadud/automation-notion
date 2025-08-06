#!/bin/bash

# Moodle Assignment Fetcher - Daily Cron Script
# Add this to your crontab to run daily at 9 AM:
# 0 9 * * * /path/to/automate/daily_check.sh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Use virtual environment Python if it exists
if [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Run the fetcher
$PYTHON_CMD run_fetcher.py --days 1 >> daily_check.log 2>&1

# Log the execution
echo "$(date): Daily check completed" >> daily_check.log
