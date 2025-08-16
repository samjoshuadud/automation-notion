# 🎓 Moodle Assignment Fetcher

A powerful, automated system for fetching assignments directly from Moodle and syncing them to Notion and Todoist. Built with Python and modern web scraping technologies.

## ✨ What This System Does

- **🔍 Direct Moodle Scraping**: Logs into your Moodle account and fetches assignments directly from the course pages
- **📝 Notion Integration**: Automatically syncs assignments to your Notion database with smart duplicate detection
- **✅ Todoist Integration**: Creates tasks in Todoist with due dates and course information
- **🔄 Smart Archiving**: Automatically cleans up completed assignments with configurable retention
- **🎯 Duplicate Prevention**: Uses advanced fuzzy matching to prevent duplicate assignments
- **📊 Status Management**: Tracks assignment progress across all platforms
- **🛡️ Robust Error Handling**: Comprehensive logging and error recovery

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Environment Configuration

Create a `.env` file with:

```bash
# Moodle Configuration
MOODLE_URL=https://your-moodle-site.com
MOODLE_USERNAME=your_username
MOODLE_PASSWORD=your_password

# Notion Integration (Optional)
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id

# Todoist Integration (Optional)
TODOIST_API_TOKEN=your_todoist_api_token
TODOIST_PROJECT_NAME=Assignments
```

### 3. Test Your Setup

```bash
# Test all integrations
python run_fetcher.py --test --verbose
```

### 4. Fetch Your First Assignments

```bash
# Basic fetch from Moodle
python run_fetcher.py

# Fetch with Notion sync
python run_fetcher.py --notion --verbose

# Fetch with Todoist sync
python run_fetcher.py --todoist --verbose

# Fetch with both platforms
python run_fetcher.py --notion --todoist --verbose
```

## 📋 Available Commands

### Basic Operations

```bash
# Fetch assignments from Moodle
python run_fetcher.py

# Test connections only
python run_fetcher.py --test

# Run in headless mode (no browser GUI)
python run_fetcher.py --headless
```

### Platform Integration

```bash
# Sync to Notion
python run_fetcher.py --notion

# Sync to Todoist
python run_fetcher.py --todoist

# Sync to both platforms
python run_fetcher.py --notion --todoist
```

### Data Management

```bash
# Archive cleanup (default: 30 days)
python run_fetcher.py --cleanup

# Custom cleanup period
python run_fetcher.py --cleanup --cleanup-days 60

# Show archive statistics
python run_fetcher.py --archive-stats

# Restore from archive
python run_fetcher.py --restore "Assignment Title"

# Manual archive
python run_fetcher.py --manual-archive "Assignment Title"

# Show status report
python run_fetcher.py --status-report

# Show duplicate analysis
python run_fetcher.py --show-duplicates
```

### Advanced Operations

```bash
# Clear stored Moodle session
python run_fetcher.py --clear-moodle-session

# Set Moodle URL via command line
python run_fetcher.py --moodle-url "https://your-site.com"

# Debug mode with maximum detail
python run_fetcher.py --debug

# Quiet mode (minimal output)
python run_fetcher.py --quiet
```

### Data Management (Advanced)

```bash
# Delete all assignments (with confirmation)
python run_fetcher.py --delete-all-assignments

# Selective deletion
python run_fetcher.py --delete-from notion
python run_fetcher.py --delete-from todoist
python run_fetcher.py --delete-from both

# Include local database in deletion
python run_fetcher.py --delete-from both --include-local

# Fresh start (delete all data files)
python run_fetcher.py --fresh-start
```

## 🔧 Configuration

### Notion Database Setup

Your Notion database must have these properties:

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Assignment title |
| Course | Text | Course name |
| Due Date | Date | Assignment due date |
| Status | Select | Pending/In Progress/Completed |
| Course Code | Text | Course code (e.g., CS101) |
| Added Date | Date | When assignment was added |
| Email ID | Text | Unique identifier |

### Todoist Project

- Creates/uses a project named "Assignments" (configurable)
- Maps assignment fields to task properties
- Supports due dates and descriptions

## 📁 Project Structure

```
automate/
├── run_fetcher.py              # Main application
├── moodle_direct_scraper.py    # Moodle scraping logic
├── notion_integration.py       # Notion API integration
├── todoist_integration.py      # Todoist API integration
├── assignment_archive.py       # Archive management
├── shared_utils.py             # Common utilities
├── requirements.txt            # Dependencies
├── .env                        # Configuration
├── data/                       # Data storage
├── logs/                       # Application logs
├── tests/                      # Test suite
└── documentation/              # Detailed guides
```

## 🧪 Testing

```bash
# Test all integrations
python run_fetcher.py --test --verbose

# Test specific integration
python -c "from notion_integration import NotionIntegration; n = NotionIntegration(); print('✅ Connected!' if n.enabled else '❌ Failed')"
```

## 🔍 Troubleshooting

### Common Issues

- **Moodle Connection**: Use `--clear-moodle-session` to reset stored credentials
- **Notion Sync**: Verify database schema and integration permissions
- **Todoist Sync**: Check API token and project access

### Debug Mode

```bash
# Enable maximum detail logging
python run_fetcher.py --debug

# Check logs
tail -f logs/moodle_fetcher.log
```

## 📚 Documentation

- **[Notion Integration Guide](documentation/notion-guide.md)** - Complete Notion setup
- **[Todoist Integration Guide](documentation/todoist-guide.md)** - Todoist configuration
- **[Testing Guide](documentation/testing-guide.md)** - Testing instructions

---

**Happy Assignment Management! 🎓✨**
