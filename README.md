# 🎓 Moodle Assignment Fetcher (Todoist only)

A powerful, automated system for fetching assignments directly from Moodle and syncing them to Todoist. Built with Python and modern web scraping technologies.

## ✨ What This System Does

- **🔍 Direct Moodle Scraping**: Logs into your Moodle account and fetches assignments directly from the course pages
- **✅ Todoist Integration**: Creates tasks in Todoist with due dates and course information
- **🔄 Smart Archiving**: Automatically cleans up completed assignments with configurable retention
- **🎯 Smart Change Detection**: Detects and updates existing tasks instead of creating duplicates
- **🔄 Intelligent Updates**: Monitors for deadline changes, title updates, and other modifications
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

# Todoist Integration
TODOIST_API_TOKEN=your_todoist_api_token
TODOIST_PROJECT_NAME=Assignments
```

### 3. Test Your Setup

```bash
# Test Todoist integration
python run_fetcher.py --test --verbose --todoist
```

### 4. Fetch Your First Assignments

```bash
# Basic fetch from Moodle
python run_fetcher.py

# Fetch with Todoist sync
python run_fetcher.py --todoist --verbose
```

## 🔄 Smart Change Detection

The system now intelligently detects changes in existing Moodle tasks and updates them instead of creating duplicates. This handles common scenarios like:

- **📅 Deadline Changes**: Professors extend or shorten assignment due dates
- **✏️ Title Updates**: Assignment names are modified or corrected
- **📊 Status Changes**: Completion status updates from Moodle
- **🔗 URL Changes**: Moodle structure updates affecting assignment links
- **📝 Activity Type Changes**: Quizzes converted to assignments or vice versa

### How It Works

1. **Smart Matching**: Uses `task_id` as primary identifier, falls back to title + course matching
2. **Change Detection**: Compares all relevant fields between scraped and existing data
3. **Selective Updates**: Only updates fields that have actually changed
4. **Comprehensive Logging**: Records all changes for monitoring and debugging

### Change Detection Methods

```python
# Preview changes before merging
scraper.manual_scrape(show_changes=True)

# Check for changes and optionally auto-update
scraper.check_for_changes(auto_update=True)

# Compare scraped vs existing tasks
comparison = scraper.compare_scraped_with_existing()

# Get summary of last merge operation
summary = scraper.get_change_summary()
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

### Platform Integration (Todoist)

```bash
# Sync to Todoist
python run_fetcher.py --todoist
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
python run_fetcher.py --delete-from todoist

# Include local database in deletion
python run_fetcher.py --delete-from both --include-local

# Fresh start (delete all data files)
python run_fetcher.py --fresh-start
```

## 🔧 Configuration

### Todoist Project

- Creates/uses a project named "Assignments" (configurable)
- Maps assignment fields to task properties
- Supports due dates and descriptions

## 📁 Project Structure

```
automate/
├── run_fetcher.py              # Main application
├── moodle_direct_scraper.py    # Moodle scraping logic
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
# Test Todoist integration
python run_fetcher.py --test --verbose --todoist
```

## 🔍 Troubleshooting

### Common Issues

- **Moodle Connection**: Use `--clear-moodle-session` to reset stored credentials
- **Todoist Sync**: Check API token and project access

### Debug Mode

```bash
# Enable maximum detail logging
python run_fetcher.py --debug

# Check logs
tail -f logs/moodle_fetcher.log
```

## 📚 Documentation

- **[Todoist Integration Guide](documentation/todoist-guide.md)** - Todoist configuration
- **[Testing Guide](documentation/testing-guide.md)** - Testing instructions

---

**Happy Assignment Management! 🎓✨**
