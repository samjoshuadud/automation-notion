# Setup Instructions for Moodle Assignment Email Fetcher

## Prerequisites Completed ✅

- Python 3.6+ installed
- Virtual environment created
- Dependencies installed (python-dotenv, requests)
- All scripts configured

## Next Steps

### 1. Configure Gmail Access

1. **Enable 2-Factor Authentication** on your Google account if not already enabled

2. **Generate Gmail App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Navigate to **Security** → **2-Step Verification** → **App passwords**
   - Select "Mail" as the app and generate a 16-character password
   - **Save this password** - you won't see it again!

3. **Update Environment File**:
   ```bash
   # Copy the template
   cp .env.example .env
   
   # Edit with your details
   nano .env  # or use your preferred editor
   ```
   
   Update these fields in `.env`:
   ```env
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_character_app_password
   SCHOOL_DOMAIN=yourschool.edu  # Replace with your school's domain
   ```

### 2. Test the Setup

```bash
# Activate virtual environment (for fish shell)
source venv/bin/activate.fish

# Test Gmail connection
python3 run_fetcher.py --test

# If successful, try a real check
python3 run_fetcher.py --days 7 --verbose
```

### 3. Set Up Automated Daily Checks

#### Option A: Cron Job (Recommended)

```bash
# Open crontab editor
crontab -e

# Add this line to run daily at 9 AM:
0 9 * * * /home/punisher/Documents/automate/daily_check.sh

# Or run every 6 hours:
0 */6 * * * /home/punisher/Documents/automate/daily_check.sh
```

#### Option B: Manual Running

```bash
# Check for assignments from last 3 days
source venv/bin/activate.fish && python3 run_fetcher.py --days 3

# With verbose output
source venv/bin/activate.fish && python3 run_fetcher.py --days 3 --verbose
```

### 4. Optional: Notion Integration

If you want to sync assignments to Notion:

1. **Create Notion Integration**:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Click "New integration"
   - Name it "Moodle Fetcher" and create

2. **Create Notion Database**:
   - Create a new page in Notion
   - Add a database with these properties:
     - `Assignment` (Title)
     - `Due Date` (Date)
     - `Course` (Text) 
     - `Status` (Select with options: Pending, In Progress, Completed)
     - `Source` (Text)

3. **Connect Integration**:
   - In your database page, click "Share"
   - Add your integration

4. **Update .env**:
   ```env
   NOTION_TOKEN=secret_your_integration_token
   NOTION_DATABASE_ID=your_database_id_from_url
   ```

5. **Test Notion sync**:
   ```bash
   source venv/bin/activate.fish
   python3 run_fetcher.py --notion --test
   ```

## Usage Examples

```bash
# Always activate virtual environment first (for fish shell)
source venv/bin/activate.fish

# Basic check (last 7 days)
python3 run_fetcher.py

# Check specific time range
python3 run_fetcher.py --days 14

# With Notion sync
python3 run_fetcher.py --notion

# Verbose logging
python3 run_fetcher.py --verbose

# Test mode (just check connections)
python3 run_fetcher.py --test
```

## Output Files

The script creates:

- `assignments.json` - Machine-readable assignment data
- `assignments.md` - Human-readable Markdown table
- `moodle_fetcher.log` - Detailed execution logs
- `daily_check.log` - Cron job execution logs

## Troubleshooting

### "Gmail credentials not found"
- Verify `.env` file exists in the project directory
- Check that `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` are set
- Ensure App Password is exactly 16 characters

### "No emails found"
- Verify `SCHOOL_DOMAIN` matches your school's email domain
- Check that Moodle emails are in your Gmail inbox (not spam)
- Try increasing the `--days` parameter
- Use `--verbose` flag to see detailed search information

### Virtual Environment Issues
```bash
# Recreate virtual environment if needed
rm -rf venv
python3 -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
```

### Cron Job Not Running
```bash
# Check cron service is running
systemctl status cronie  # Arch Linux
# or
systemctl status cron    # Ubuntu/Debian

# Check cron logs
journalctl -u cronie
# or check
tail -f /var/log/cron
```

## File Structure

```
/home/punisher/Documents/automate/
├── venv/                    # Python virtual environment
├── .env                     # Your credentials (create from .env.example)
├── .env.example            # Template for credentials
├── requirements.txt        # Python dependencies
├── moodle_fetcher.py      # Main email fetching logic
├── notion_integration.py  # Notion API integration
├── run_fetcher.py         # Command-line interface
├── daily_check.sh         # Cron script
├── setup.py              # Setup script
├── README.md             # Full documentation
├── SETUP.md              # This file
├── assignments.json      # Generated: Assignment data
├── assignments.md        # Generated: Assignment table
├── moodle_fetcher.log   # Generated: Detailed logs
└── daily_check.log      # Generated: Cron logs
```

## Security Notes

- Never commit your `.env` file to version control
- Regularly rotate your Gmail App Password
- The App Password only works with 2FA enabled
- Store your credentials securely

## Success Indicators

When working correctly, you should see:
- ✅ "Gmail connection successful!" during tests
- New entries in `assignments.json` and `assignments.md`
- Log entries in `moodle_fetcher.log`
- Cron execution logs in `daily_check.log`

Your Moodle Assignment Email Fetcher is ready to use! 🎉
