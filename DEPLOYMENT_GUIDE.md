# Moodle Assignment Email Fetcher - Enhanced Setup Guide

## Overview
This enhanced system automatically fetches Moodle assignment emails from Gmail, extracts assignment details using improved regex patterns, and optionally syncs to Notion with reminder functionality.

## Features
- ✅ Enhanced regex patterns for better email parsing
- ✅ Smart title formatting: "coursecode - activity no. (name)"
- ✅ Robust error handling and fallbacks
- ✅ Notion integration with 3-day reminders
- ✅ Duplicate detection
- ✅ Comprehensive logging
- ✅ Production-ready deployment scripts

## Quick Start

### 1. Environment Setup
```bash
# Clone or copy files to your directory
cd /home/punisher/Documents/automate

# Create virtual environment
python -m venv venv

# Activate virtual environment (Fish shell)
source venv/bin/activate.fish

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials
```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required Environment Variables:**
```bash
# Gmail settings
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password

# School domain (for UMak)
SCHOOL_DOMAIN=umak.edu.ph

# Optional: Notion integration
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
```

### 3. Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Use the 16-character password in `.env`

### 4. Notion Setup (Optional)
1. Create a Notion integration at https://www.notion.so/my-integrations
2. Create a database with these properties:
   - **Assignment** (Title)
   - **Due Date** (Date)
   - **Course** (Rich Text)
   - **Course Code** (Rich Text)
   - **Status** (Select: Pending, In Progress, Completed)
   - **Source** (Rich Text)
   - **Reminder Date** (Date)
3. Share your database with the integration
4. Copy the database ID from the URL

## Usage

### Test Connection
```bash
python run_fetcher.py --test --notion
```

### Run Assignment Check
```bash
# Basic check (last 7 days)
python run_fetcher.py

# Check last 14 days with Notion sync
python run_fetcher.py --days 14 --notion

# Verbose logging
python run_fetcher.py --verbose --notion

# Skip Notion even if configured
python run_fetcher.py --skip-notion
```

### Test Email Parsing
```bash
python test_parsing.py
```

## Enhanced Features

### 1. Smart Title Formatting
The system now formats assignment titles according to your requirements:
- Input: "ACTIVITY 1 - USER STORY" 
- Output: "hci - activity 1 (user story)"

### 2. Improved Date Parsing
Supports multiple date formats:
- "Friday, 5 September 2025, 10:09 AM"
- "September 5, 2025"
- "2025-09-05"
- "05/09/2025"

### 3. Error Handling & Fallbacks
- Connection timeouts and retries
- Graceful degradation when services fail
- Detailed logging for debugging
- Fallback patterns for parsing

### 4. Notion Reminders
- Automatically sets reminder 3 days before due date
- Prevents duplicate entries
- Robust API error handling

## Deployment for Production

### 1. Automated Daily Checks
```bash
# Run the daily check script
./daily_check.sh

# Or use the quick start script
./quick_start.sh
```

### 2. Cron Job Setup
```bash
# Edit crontab
crontab -e

# Add daily check at 8 AM
0 8 * * * /home/punisher/Documents/automate/daily_check.sh

# Add hourly check during business hours
0 9-17 * * 1-5 /home/punisher/Documents/automate/daily_check.sh
```

### 3. Systemd Service (Recommended)
```bash
# Create service file
sudo nano /etc/systemd/system/moodle-fetcher.service
```

Content:
```ini
[Unit]
Description=Moodle Assignment Fetcher
After=network.target

[Service]
Type=oneshot
User=punisher
WorkingDirectory=/home/punisher/Documents/automate
ExecStart=/home/punisher/Documents/automate/daily_check.sh
Environment=PATH=/home/punisher/Documents/automate/venv/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
```

```bash
# Create timer
sudo nano /etc/systemd/system/moodle-fetcher.timer
```

Content:
```ini
[Unit]
Description=Run Moodle Assignment Fetcher daily
Requires=moodle-fetcher.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Enable and start
sudo systemctl enable moodle-fetcher.timer
sudo systemctl start moodle-fetcher.timer

# Check status
sudo systemctl status moodle-fetcher.timer
```

## File Structure
```
automate/
├── moodle_fetcher.py          # Main email fetching logic
├── notion_integration.py      # Enhanced Notion integration
├── run_fetcher.py            # CLI interface
├── test_parsing.py           # Test email parsing
├── daily_check.sh            # Daily automation script
├── quick_start.sh            # Quick setup script
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .env                     # Your credentials (create this)
├── assignments.json         # Local storage
├── assignments.md          # Markdown output
├── moodle_fetcher.log      # Log file
└── venv/                   # Virtual environment
```

## Monitoring and Logs

### View Logs
```bash
# Real-time log monitoring
tail -f moodle_fetcher.log

# Last 50 log entries
tail -n 50 moodle_fetcher.log

# Search for errors
grep -i error moodle_fetcher.log
```

### Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/moodle-fetcher
```

Content:
```
/home/punisher/Documents/automate/moodle_fetcher.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 punisher punisher
}
```

## Troubleshooting

### Common Issues

1. **Gmail Authentication Failed**
   - Ensure 2FA is enabled
   - Use App Password, not regular password
   - Check GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env

2. **No Emails Found**
   - Verify SCHOOL_DOMAIN matches your school's emails
   - Check email search date range
   - Use --verbose for detailed logging

3. **Notion Integration Issues**
   - Verify NOTION_TOKEN and NOTION_DATABASE_ID
   - Ensure database is shared with integration
   - Check database properties match expected format

4. **Parsing Issues**
   - Run test_parsing.py to verify regex patterns
   - Check moodle_fetcher.log for parsing details
   - Email format may have changed - update regex patterns

### Debug Mode
```bash
# Run with maximum verbosity
python run_fetcher.py --verbose --test

# Test specific functionality
python test_parsing.py
```

## Security Notes

- Keep `.env` file secure and never commit to version control
- Use App Passwords instead of main Gmail password
- Regularly rotate credentials
- Monitor logs for unauthorized access attempts
- Consider using encrypted storage for sensitive data

## Performance Optimization

- Default check: last 7 days (adjust with --days)
- Notion API has rate limits (handled automatically)
- Consider running less frequently for large email volumes
- Log rotation prevents disk space issues

## Support

For issues or questions:
1. Check the logs: `tail -f moodle_fetcher.log`
2. Run tests: `python test_parsing.py`
3. Test connections: `python run_fetcher.py --test --notion`
4. Review this guide for troubleshooting steps
