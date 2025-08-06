# Moodle Assignment Email Fetcher

A Python script that automatically checks your Gmail inbox for Moodle assignment emails, extracts assignment details, and saves them to local files or syncs with Notion.

## Features

- ✅ **Free and Open Source** - No paid APIs required
- 📧 **Gmail Integration** - Uses IMAP with App Passwords
- 🎯 **Smart Parsing** - Regex-based extraction of assignment details
- 📝 **Multiple Output Formats** - JSON and Markdown files
- 🔄 **Duplicate Detection** - Prevents duplicate assignments
- 📅 **Scheduled Checks** - Daily cron support
- 🔗 **Notion Integration** - Optional sync to Notion (free tier)
- 🐧 **Linux Compatible** - Tested on Ubuntu/Arch Linux

## Quick Start

### 1. Setup

```bash
# Clone or download the files to your desired directory
cd /home/punisher/Documents/automate

# Install dependencies
pip3 install python-dotenv requests

# Copy environment template
cp .env.example .env
```

### 2. Configure Gmail

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Update .env file**:
   ```env
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_character_app_password
   SCHOOL_DOMAIN=yourschool.edu
   ```

### 3. Test Connection

```bash
python3 run_fetcher.py --test
```

### 4. Run Manual Check

```bash
# Check last 7 days
python3 run_fetcher.py

# Check last 3 days
python3 run_fetcher.py --days 3

# With verbose logging
python3 run_fetcher.py --verbose
```

## Scheduled Execution

### Option 1: Cron (Recommended)

```bash
# Make script executable
chmod +x daily_check.sh

# Add to crontab (runs daily at 9 AM)
crontab -e

# Add this line:
0 9 * * * /home/punisher/Documents/automate/daily_check.sh
```

### Option 2: Loop Script

```bash
# Run continuous loop (checks every 24 hours)
while true; do
    python3 run_fetcher.py --days 1
    sleep 86400  # 24 hours
done
```

## Output Files

The script creates two output files:

### `assignments.json`
```json
[
  {
    "title": "Physics Lab Report 3",
    "due_date": "2025-08-15",
    "course": "PHYS 201",
    "status": "Pending",
    "source": "email",
    "added_date": "2025-08-07 10:30:00"
  }
]
```

### `assignments.md`
```markdown
# Moodle Assignments

| Assignment | Due Date | Course | Status | Added Date |
|------------|----------|--------|--------|-----------|
| Physics Lab Report 3 | 2025-08-15 | PHYS 201 | Pending | 2025-08-07 10:30:00 |
```

## Notion Integration (Optional)

### Setup Notion Database

1. **Create Integration**:
   - Go to https://www.notion.so/my-integrations
   - Create new integration
   - Copy the token

2. **Create Database**:
   - Create a new Notion page with a database
   - Add these properties:
     - `Assignment` (Title)
     - `Due Date` (Date)
     - `Course` (Text)
     - `Status` (Select: Pending, In Progress, Completed)
     - `Source` (Text)

3. **Share Database**:
   - Click "Share" on your database
   - Add your integration

4. **Update .env**:
   ```env
   NOTION_TOKEN=your_integration_token
   NOTION_DATABASE_ID=your_database_id
   ```

### Use with Notion

```bash
# Sync to Notion
python3 run_fetcher.py --notion

# Test Notion connection
python3 run_fetcher.py --test --notion
```

## Regex Patterns

The script uses smart regex patterns to extract:

- **Assignment Titles**:
  - "Assignment submission: [Title]"
  - "Assignment: [Title]"
  - "New assignment: [Title]"

- **Due Dates**:
  - "Due date: [Date]"
  - "Due: [Date]"
  - "Deadline: [Date]"

- **Course Names**:
  - "Course: [Name]"
  - "in course [Name]"

## Troubleshooting

### Common Issues

1. **"Gmail credentials not found"**
   - Check your `.env` file exists and has correct credentials
   - Verify App Password is 16 characters

2. **"No emails found"**
   - Verify your school domain in `.env`
   - Check if Moodle emails are in your inbox
   - Try increasing `--days` parameter

3. **"Permission denied" for daily_check.sh**
   ```bash
   chmod +x daily_check.sh
   ```

4. **Python module errors**
   ```bash
   pip3 install --user python-dotenv requests
   ```

### Logs

- Check `moodle_fetcher.log` for detailed logs
- Check `daily_check.log` for cron execution logs

## Customization

### Add New Regex Patterns

Edit the `patterns` dictionary in `moodle_fetcher.py`:

```python
'title_patterns': [
    r'Your custom pattern: (.+?)(?:\n|$)',
    # Add more patterns
]
```

### Change Output Format

Modify the `save_assignments()` method to customize output format.

### Add Other Email Providers

The script can be adapted for other email providers by changing the IMAP settings in `connect_to_gmail()`.

## Security Notes

- Store `.env` file securely (never commit to git)
- Use App Passwords instead of your main password
- Regularly rotate your App Password

## License

This project is free to use and modify for personal and educational purposes.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Review log files
3. Verify your Gmail and Notion setup
4. Test with `--test` flag first
