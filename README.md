# Moodle Assignment Automation System

A production-ready automation system that fetches Moodle assignment emails from Gmail, parses and deduplicates assignments, stores them locally, and syncs them to a Notion database with intelligent status-based archiving.

## 🚀 Features

- **Automated Email Fetching**: Connects to Gmail and fetches assignment emails from Moodle
- **Intelligent Parsing**: Extracts assignment details using advanced regex patterns
- **Robust Duplicate Detection**: Uses email ID, normalized titles, and fuzzy matching
- **Local Storage**: Maintains assignments in JSON format with append-only logic
- **Notion Integration**: Two-way sync with Notion database including status updates
- **Todoist Integration**: Sync assignments to Todoist as tasks with smart reminders and bidirectional status sync
- **Status-Based Archiving**: Automatically archives completed assignments after 30 days
- **Smart Restore**: Restores archived assignments if status changes in Notion
- **Comprehensive Error Handling**: Graceful failure recovery and detailed logging
- **Production Deployment**: Ready for cron/systemd scheduling

## 📁 Project Structure

```
moodle-assignment-automation/
├── 📄 Main Scripts
│   ├── run_fetcher.py           # Main entry point
│   ├── moodle_fetcher.py        # Gmail fetching and parsing
│   ├── notion_integration.py    # Notion API integration
│   ├── todoist_integration.py   # Todoist API integration
│   └── assignment_archive.py    # Archive management system
│
├── 📂 data/                     # Data storage
│   ├── assignments.json         # Active assignments
│   ├── assignments_archive.json # Archived assignments
│   └── *.json                   # Other data files
│
├── 🧪 tests/                    # Testing and setup
│   ├── setup_notion_db.py       # Notion database setup
│   ├── test_parsing.py          # Test email parsing
│   ├── test_real_parsing.py     # Test with real emails
│   └── test_notion_sync.py      # Test Notion integration
│
├── 🚀 deployment/               # Production deployment
│   ├── daily_check.sh           # Cron script
│   ├── deploy.sh               # Setup script
│   ├── moodle-fetcher.service  # Systemd service
│   └── moodle-fetcher.timer    # Systemd timer
│
└── 📋 Configuration
    ├── .env                     # Your credentials (create from .env.example)
    ├── .env.example            # Template for credentials
    ├── requirements.txt        # Python dependencies
    └── README.md              # This file
```

## ⚡ Quick Start (5 Minutes)

**New to this? Follow these 5 simple steps:**

1. **Download and Setup**
   ```bash
   # Download this repository and navigate to it
   cd moodle-assignment-automation
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Gmail**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gmail credentials (see Step 2 below for details)
   ```

3. **Test Connection**
   ```bash
   python run_fetcher.py --test
   # Should show: ✅ Gmail connection successful!
   ```

4. **Fetch Your First Assignments**
   ```bash
   python run_fetcher.py
   # Fetches assignments from last 7 days into data/assignments.json
   ```

5. **Optional: Setup Notion or Todoist**
   ```bash
   # For Notion integration
   python tests/setup_notion_db.py
   
   # For Todoist integration  
   python tests/setup_todoist.py
   
   # Follow the guides to sync with your preferred task manager
   ```

**That's it! Your assignments are now in `data/assignments.json`** 📋

---

## 📋 Table of Contents

1. [Quick Start (5 Minutes)](#-quick-start-5-minutes)
2. [Project Structure](#-project-structure)
3. [Installation & Setup](#-quick-start-guide)
4. [How to Use](#-how-to-use-the-script)
5. [Common Examples](#-common-usage-examples)
6. [Automation Flow](#-automation-flow)
7. [Archive Management](#-archive-management)
8. [Error Handling](#-error-handling)
9. [Deployment](#-deployment)
10. [Troubleshooting](#-troubleshooting)
11. [API Reference](#-api-reference)

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gmail API     │    │  Local Storage   │    │  Notion API     │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ assignments.json │    │ Database Pages  │
│ │Assignment   │ │◄──►│ assignments_     │◄──►│ Properties      │
│ │Emails       │ │    │ archive.json     │    │ Status Updates  │
│ └─────────────┘ │    └──────────────────┘    └─────────────────┘
└─────────────────┘                             
        │                                               
        ▼                                               
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Email Parser    │    │ Archive Manager  │    │ Status Sync     │
│                 │    │                  │    │                 │
│ • Regex Extract │    │ • Auto Archive   │    │ • Bi-directional│
│ • Normalize     │    │ • Smart Restore  │    │ • Status Match  │
│ • Duplicate Det │    │ • Manual Control │    │ • Conflict Res  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

1. **MoodleEmailFetcher** (`moodle_fetcher.py`)
   - Gmail connection and email retrieval
   - Assignment parsing and extraction
   - Duplicate detection and deduplication
   - Local JSON storage management

2. **NotionIntegration** (`notion_integration.py`)
   - Notion API connectivity
   - Assignment synchronization
   - Status tracking and updates
   - Duplicate prevention in Notion

3. **AssignmentArchiveManager** (`assignment_archive.py`)
   - Status-based archiving system
   - Smart restoration logic
   - Archive statistics and management
   - Bi-directional status synchronization

4. **Main Runner** (`run_fetcher.py`)
   - Command-line interface
   - Workflow orchestration
   - Error handling and logging
   - Automated scheduling support

## 🛠️ Quick Start Guide

### Step 1: Clone and Setup Environment

```bash
# Clone or download this repository
git clone <repository-url>
cd moodle-assignment-automation

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR for fish shell: source venv/bin/activate.fish

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Gmail Credentials

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and generate a 16-character password
3. **Setup Environment File**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

Edit `.env` file:
```env
# Gmail Configuration (Required)
GMAIL_EMAIL=your.email@umak.edu.ph
GMAIL_APP_PASSWORD=your_16_character_app_password

# School Domain Configuration  
SCHOOL_DOMAIN=umak.edu.ph

# Notion Integration (Optional)
NOTION_TOKEN=secret_xyz123...
NOTION_DATABASE_ID=your_database_id

# Todoist Integration (Optional)
TODOIST_TOKEN=your_todoist_api_token
```

### Step 3: Setup Notion Database (Optional)

```bash
# Run the Notion setup helper
python tests/setup_notion_db.py
```

Follow the instructions to:
1. Create a Notion integration at https://www.notion.so/my-integrations
2. Create a database with required properties
3. Share the database with your integration
4. Add credentials to `.env` file

### Step 3b: Setup Todoist Integration (Optional)

```bash
# Run the Todoist setup helper
python tests/setup_todoist.py
```

Follow the instructions to:
1. Get your Todoist API token from https://todoist.com/prefs/integrations
2. Add TODOIST_TOKEN to your `.env` file
3. Test the integration

**Todoist Free Tier Features:**
- ✅ Works with free Todoist account
- ✅ Assignments become tasks with due dates
- ✅ Course codes become task labels
- ✅ Cross-platform sync (mobile, web, desktop)
- ✅ No premium subscription required

### Step 4: Test Your Setup

```bash
# Test Gmail and Notion connections
python run_fetcher.py --test

# Expected output:
# ✅ Gmail connection successful!
# ✅ Notion integration configured and connected!
```

### Step 5: Run Your First Fetch

```bash
# Fetch assignments from last 7 days
python run_fetcher.py

# With Notion sync
python run_fetcher.py --notion

# With verbose logging
python run_fetcher.py --notion --verbose
```

## 📖 How to Use the Script

### Basic Commands

```bash
# Fetch new assignments (last 7 days)
python run_fetcher.py

# Fetch with Notion synchronization
python run_fetcher.py --notion

# Fetch with Todoist synchronization
python run_fetcher.py --todoist

# Fetch with both Notion and Todoist synchronization
python run_fetcher.py --notion --todoist

# Fetch from specific time range (last 14 days)
python run_fetcher.py --days 14 --todoist

# Test connections only (no fetching)
python run_fetcher.py --test

# Enable verbose logging for debugging
python run_fetcher.py --verbose --todoist
```

### Archive Management

```bash
# View archive statistics
python run_fetcher.py --archive-stats

# Manual cleanup (archive completed assignments older than 30 days)
python run_fetcher.py --cleanup --cleanup-days 30

# Restore specific assignment from archive
python run_fetcher.py --restore "Assignment Title"

# Manually archive an assignment
python run_fetcher.py --manual-archive "Assignment Title"
```

### Testing and Setup

```bash
# Setup Notion database properties
python tests/setup_notion_db.py

# Setup Todoist integration
python tests/setup_todoist.py

# Test email parsing with sample data
python tests/test_parsing.py

# Test with real emails from your Gmail
python tests/test_real_parsing.py

# Test Notion synchronization
python tests/test_notion_sync.py

# Test Todoist synchronization
python tests/test_todoist_sync.py
```

### Production Deployment

```bash
# Setup automated execution (every 2 hours + nightly)
chmod +x deployment/daily_check.sh

# Option 1: Cron job (simple)
crontab -e
# Add: 0 8,10,12,14,16,18 * * * /path/to/automate/deployment/daily_check.sh

# Option 2: Systemd service (recommended)
sudo cp deployment/moodle-fetcher.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable moodle-fetcher.timer
sudo systemctl start moodle-fetcher.timer
```

## 🎯 Choosing Your Integration

### Notion vs Todoist

| Feature | Notion | Todoist |
|---------|--------|---------|
| **Free Tier** | Limited blocks | Full task management |
| **Best For** | Detailed project tracking | Quick task management |
| **Mobile App** | Good | Excellent |
| **Offline Access** | Limited | Full offline sync |
| **Due Date Alerts** | Basic | Advanced notifications |
| **Learning Curve** | Moderate | Easy |
| **Status Sync** | Two-way | One-way (to Todoist) |

### Recommended Setups

**🎓 Student (Free Tier Focus):**
```bash
python run_fetcher.py --todoist
```
- Use Todoist for daily task management
- Great mobile app with notifications
- Works perfectly with free account

**📊 Advanced User:**
```bash
python run_fetcher.py --notion --todoist  
```
- Notion for detailed project tracking
- Todoist for quick daily task management
- Best of both worlds

**💼 Simple Setup:**
```bash
python run_fetcher.py --notion
```
- Everything in one place
- Good for desktop-focused workflow

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Gmail Configuration (Required)
GMAIL_EMAIL=your.email@umak.edu.ph
GMAIL_APP_PASSWORD=your_16_char_app_password

# School Domain Configuration
SCHOOL_DOMAIN=umak.edu.ph

# Notion Integration (Optional)
NOTION_TOKEN=secret_xyz123...
NOTION_DATABASE_ID=your_database_id
```

### Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate an app password for "Mail"
4. Use the 16-character password in your `.env` file

### Todoist API Token Setup

1. Go to [Todoist Integrations](https://todoist.com/prefs/integrations)
2. Find your API token (long string of characters)
3. Copy the token and add it to your `.env` file as `TODOIST_TOKEN=your_token_here`
4. No premium subscription required - works with free accounts!

### Notion Database Setup

Required properties in your Notion database:

| Property Name | Type | Options |
|---------------|------|---------|
| Assignment | Title | - |
| Due Date | Date | - |
| Course | Rich Text | - |
| Course Code | Rich Text | - |
| Status | Select | Pending, In Progress, Completed |
| Source | Rich Text | - |
| Reminder Date | Date | - |

## 📖 Usage Guide

### Command Line Interface

```bash
# Basic fetch (last 7 days)
python run_fetcher.py

# Fetch with Notion sync
python run_fetcher.py --notion

# Test connections only
python run_fetcher.py --test

# Fetch specific time range
python run_fetcher.py --days 14 --notion

# Archive management
python run_fetcher.py --cleanup --cleanup-days 30
python run_fetcher.py --archive-stats
python run_fetcher.py --restore "Assignment Title"
python run_fetcher.py --manual-archive "Assignment Title"

# Verbose logging
python run_fetcher.py --verbose --notion
```

### Archive Management Commands

```bash
# View archive statistics
python run_fetcher.py --archive-stats

# Manual cleanup (archive completed assignments older than 30 days)
python run_fetcher.py --cleanup --cleanup-days 30

# Restore specific assignment from archive
python run_fetcher.py --restore "HCI - Activity 1 (User Story [1])"

# Manually archive an assignment
python run_fetcher.py --manual-archive "Old Assignment"
```

### Testing Scripts

```bash
# Test real-time email parsing
python test_real_parsing.py

# Test Notion synchronization
python test_notion_sync.py

# Test assignment parsing logic
python test_parsing.py
```

## 🎯 Common Usage Examples

### Daily Workflow

```bash
# Morning: Check for new assignments
python run_fetcher.py --todoist

# Or sync to both systems
python run_fetcher.py --notion --todoist

# Output example:
# ✅ Successfully found 2 new assignments!
# ✅ Synced 2 assignments to Todoist!
# 🧹 No assignments need archiving
# 🔄 Status sync: Updated 1, Restored 0 assignments
```

### Weekly Maintenance

```bash
# Check archive status
python run_fetcher.py --archive-stats

# Manual cleanup if needed
python run_fetcher.py --cleanup --cleanup-days 30

# Restore assignment if accidentally archived
python run_fetcher.py --restore "Assignment Title"
```

### Troubleshooting

```bash
# Debug parsing issues
python tests/test_real_parsing.py

# Debug Notion connection
python tests/test_notion_sync.py

# Debug Todoist connection
python tests/test_todoist_sync.py

# Verbose logging for debugging
python run_fetcher.py --verbose --test
```

### Production Setup

```bash
# One-time setup for automated execution
chmod +x deployment/daily_check.sh

# Add to crontab for every 2 hours during day + night check
crontab -e
# Add: 0 8,10,12,14,16,18 * * * /path/to/automate/deployment/daily_check.sh
# Add: 0 2 * * * /path/to/automate/deployment/daily_check.sh
```

## 🔄 Automation Flow

### 1. Email Fetching Phase

**Process Details:**
- Connects to Gmail using IMAP with app password
- Searches for emails from `noreply-tbl@umak.edu.ph`
- Filters emails within specified date range (default: 7 days)
- Extracts assignment information using regex patterns
- Performs triple-layer duplicate detection

### 2. Duplicate Detection System

The system uses a three-tier approach:

1. **Email ID Check**: Prevents re-processing same email
2. **Normalized Title Matching**: Compares standardized titles
3. **Fuzzy Matching**: Catches similar assignments with minor differences

### 3. Notion Synchronization

**Sync Process:**
- Checks each local assignment against Notion database
- Creates missing assignments in Notion
- Retrieves status updates from Notion
- Applies status changes to local storage
- Handles archive restoration if status changed to active

### 4. Archive Management Flow

**Automatic Archiving:**
- Assignments with status "Completed" older than 30 days
- Move from `assignments.json` to `assignments_archive.json`
- Every time the main script runs
- Preserves original data and metadata

**Smart Restoration:**
- Status change in Notion from "Completed" to "Pending"/"In Progress"
- Automatically restore assignment from archive
- Sets new status and updates timestamp
- Ensures Notion and local data remain consistent

## 📁 Archive Management

### Archive File Structure

```json
{
  "created_date": "2025-08-07T00:00:00",
  "last_cleanup": "2025-08-07T01:30:00",
  "total_archived": 5,
  "assignments": [
    {
      "original_data": { /* Full assignment object */ },
      "archived_date": "2025-08-07T01:30:00",
      "archive_reason": "completed_30_days",
      "completion_date": "2025-07-01 10:00:00",
      "title": "Assignment Title",
      "course_code": "HCI"
    }
  ]
}
```

## 🛡️ Error Handling

### Connection Errors

**Gmail Connection Issues:**
- Retry logic with exponential backoff
- Clear error messages for authentication failures
- Graceful degradation when Gmail unavailable

**Notion API Errors:**
- Rate limiting with automatic backoff and retry
- Authentication error handling with guidance
- Network timeout management
- Data validation before API calls

### Data Integrity Protection

**Local Storage:**
- Atomic file operations to prevent corruption
- Backup creation before modifications
- Schema validation for JSON data
- Graceful handling of malformed files

**Duplicate Prevention:**
- Multi-layer duplicate detection
- Email ID tracking to prevent reprocessing
- Title normalization for fuzzy matching
- Date-based validation for extra confirmation

### Error Scenarios & Responses

| Scenario | Response | Recovery |
|----------|----------|----------|
| Gmail auth failure | Log error, disable Gmail | Continue with local operations |
| Notion API down | Log warning, queue for retry | Process continues, sync later |
| Local file corruption | Restore from backup | Recreate from valid data |
| Parse error | Skip problematic email | Continue with remaining emails |
| Network timeout | Retry with exponential backoff | Fail gracefully after max attempts |
| Invalid assignment data | Log validation error | Skip and continue processing |

## 🚀 Deployment

### Production Deployment Options

#### Option 1: Cron Job (Simple)

```bash
# Edit crontab
crontab -e

# Add entry for every 2 hours during active hours
0 8,10,12,14,16,18 * * * /home/user/Documents/automate/daily_check.sh
# Night check at 2 AM
0 2 * * * /home/user/Documents/automate/daily_check.sh
```

#### Option 2: Systemd Service (Recommended)

```bash
# Install service files
sudo cp moodle-fetcher.service /etc/systemd/system/
sudo cp moodle-fetcher.timer /etc/systemd/system/

# Enable and start
sudo systemctl enable moodle-fetcher.timer
sudo systemctl start moodle-fetcher.timer

# Check status
sudo systemctl status moodle-fetcher.timer
```

### Monitoring & Maintenance

**Log Monitoring:**
```bash
# View recent logs
tail -f moodle_fetcher.log

# Check for errors
grep "ERROR" moodle_fetcher.log

# Monitor service status
systemctl status moodle-fetcher.timer
```

**Health Checks:**
- Automated email parsing tests
- Notion connectivity verification
- Archive integrity validation
- Performance metrics tracking

## 🔧 Troubleshooting

### Common Issues

#### Gmail Connection Problems

**Issue**: Authentication failures
```
ERROR: Gmail connection failed: [AUTHENTICATIONFAILED]
```

**Solutions:**
1. Verify 2FA is enabled on Gmail account
2. Generate new App Password
3. Check email address in `.env` file
4. Ensure no spaces in app password

#### Notion Integration Issues

**Issue**: Database not found
```
ERROR: Notion database not found or integration not shared
```

**Solutions:**
1. Share database with your Notion integration
2. Verify database ID in URL
3. Check integration permissions
4. Confirm property names match expected format

#### Parsing Problems

**Issue**: No assignments found despite emails
```
INFO: No new assignments found
```

**Solutions:**
1. Run `python test_real_parsing.py` to debug parsing
2. Check regex patterns in `moodle_fetcher.py`
3. Verify email format matches expected patterns
4. Check date range with `--days` parameter

### Debug Commands

```bash
# Test individual components
python test_parsing.py           # Test parsing logic
python test_real_parsing.py      # Test with real emails
python test_notion_sync.py       # Test Notion integration
python setup_notion_db.py        # Verify Notion setup

# Verbose debugging
python run_fetcher.py --verbose --test

# Check archive status
python run_fetcher.py --archive-stats

# Manual operations
python run_fetcher.py --cleanup --verbose
python run_fetcher.py --restore "Assignment Title" --verbose
```

## 📚 API Reference

### MoodleEmailFetcher Class

```python
class MoodleEmailFetcher:
    def connect_to_gmail(self) -> imaplib.IMAP4_SSL
    def fetch_emails(self, days: int = 7) -> List[Dict]
    def parse_assignment_from_email(self, email_content: str) -> Optional[Dict]
    def check_duplicate(self, assignment: Dict) -> bool
    def save_assignments(self, assignments: List[Dict])
```

### NotionIntegration Class

```python
class NotionIntegration:
    def create_assignment_page(self, assignment: Dict) -> bool
    def sync_assignments(self, assignments: List[Dict]) -> int
    def assignment_exists_in_notion(self, assignment: Dict) -> bool
    def get_all_assignments_from_notion(self) -> List[Dict]
```

### AssignmentArchiveManager Class

```python
class AssignmentArchiveManager:
    def archive_completed_assignments(self, days_after_completion: int = 30) -> Dict
    def restore_assignment_from_archive(self, assignment_title: str) -> bool
    def smart_status_sync(self, notion_assignments: List[Dict]) -> Dict
    def get_archive_stats(self) -> Dict
```

## 📝 Data Formats

### Assignment Object Structure

```json
{
  "title": "HCI - Activity 1 (User Story [1])",
  "title_normalized": "hci - activity 1 (user story [1])",
  "due_date": "2025-09-05",
  "course": "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)",
  "course_code": "HCI",
  "status": "Pending",
  "source": "email",
  "raw_title": "ACTIVITY 1 - USER STORY [1]",
  "email_id": "756",
  "email_date": "Tue, 5 Aug 2025 15:34:53 +0000",
  "email_subject": "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD) content change",
  "added_date": "2025-08-07 00:46:03",
  "last_updated": "2025-08-07 00:46:03"
}
```

### Output Files

The system creates organized data files:

- **`data/assignments.json`** - Active assignments in JSON format
- **`data/assignments_archive.json`** - Archived completed assignments
- **`moodle_fetcher.log`** - Detailed execution logs with rotation

### Example Output

After running the script, you'll see:
```bash
$ python run_fetcher.py --notion

✅ Successfully found 3 new assignments!
📝 Synced 3 assignments to Notion!
🧹 Automatic cleanup: Archived 1 completed assignments
🔄 Status sync: Updated 2, Restored 0 assignments
```

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd automate
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Code Style

- Follow PEP 8 for Python code style
- Use meaningful variable and function names
- Add docstrings for all public methods
- Include type hints where appropriate
- Maintain comprehensive error handling

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check this README for common issues
2. Review log files for error details
3. Test individual components using provided scripts
4. Create an issue with detailed information if problem persists

## 🔮 Future Enhancements

- **Web Dashboard**: Browser-based interface for monitoring and control
- **Mobile Notifications**: Push notifications for new assignments
- **Calendar Integration**: Sync with Google Calendar or Outlook
- **AI-Powered Categorization**: Automatic assignment categorization
- **Performance Analytics**: Detailed metrics and reporting
- **Multi-School Support**: Support for multiple educational institutions
- **Real-time Webhooks**: Instant notifications instead of polling
- **Assignment Difficulty Estimation**: ML-based complexity analysis

---

*This automation system is designed to streamline academic assignment management while maintaining data integrity and providing comprehensive error handling for production use.*
