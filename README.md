# 🎓 Moodle Assignment Fetcher

A powerful, automated system for fetching assignments directly from Moodle and syncing them to Notion and Todoist. Built with Python and modern web scraping technologies.

## ✨ Features

- **🔍 Direct Moodle Scraping**: Bypass email notifications and fetch assignments directly from Moodle
- **📝 Notion Integration**: Automatic sync to Notion databases with smart duplicate detection
- **✅ Todoist Integration**: Create tasks in Todoist with due dates and course information
- **🔄 Smart Archiving**: Automatic cleanup of completed assignments with configurable retention
- **🎯 Duplicate Prevention**: Advanced fuzzy matching to prevent duplicate assignments
- **📊 Status Management**: Track assignment progress across all platforms
- **🛡️ Robust Error Handling**: Comprehensive logging and error recovery
- **⚡ Performance Optimized**: Efficient scraping with configurable timeouts and retries

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd automate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

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
./deployment/run.sh test

# Or test manually
python run_fetcher.py --test --verbose
```

### 4. Fetch Your First Assignments

```bash
# Basic fetch
python run_fetcher.py

# Fetch with Notion sync
python run_fetcher.py --notion --verbose

# Fetch with Todoist sync
python run_fetcher.py --todoist --verbose

# Fetch with both platforms
python run_fetcher.py --notion --todoist --verbose
```

## 📋 Core Commands

### Basic Operations

```bash
# Fetch assignments from Moodle
python run_fetcher.py

# Fetch with specific options
python run_fetcher.py --days 14 --headless --verbose

# Test connections only
python run_fetcher.py --test
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
# Archive cleanup
python run_fetcher.py --cleanup --cleanup-days 30

# Show archive statistics
python run_fetcher.py --archive-stats

# Restore from archive
python run_fetcher.py --restore "Assignment Title"

# Status report
python run_fetcher.py --status-report
```

### Advanced Operations

```bash
# Clear Moodle session
python run_fetcher.py --clear-moodle-session

# Run in headless mode
python run_fetcher.py --headless

# Debug mode with maximum detail
python run_fetcher.py --debug
```

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Moodle Site  │    │  Direct Scraper  │    │  Local Storage  │
│                 │◄───│                  │───►│  (JSON Files)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Integration    │
                       │     Layer        │
                       └──────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐      ┌──────────────┐
            │    Notion    │      │   Todoist    │
            │  Database    │      │    Tasks     │
            └──────────────┘      └──────────────┘
```

## 🔧 Configuration

### Moodle Settings

| Setting | Description | Required |
|---------|-------------|----------|
| `MOODLE_URL` | Your Moodle site URL | ✅ |
| `MOODLE_USERNAME` | Your Moodle username | ✅ |
| `MOODLE_PASSWORD` | Your Moodle password | ✅ |

### Notion Database Schema

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
├── run_fetcher.py              # Main application entry point
├── moodle_direct_scraper.py    # Core Moodle scraping logic
├── notion_integration.py       # Notion API integration
├── todoist_integration.py      # Todoist API integration
├── assignment_archive.py       # Archive management system
├── shared_utils.py             # Common utilities
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── data/                       # Data storage
│   ├── assignments.json        # Current assignments
│   └── 2fa_dom_captures/      # 2FA challenge captures
├── logs/                       # Application logs
├── tests/                      # Test suite
├── documentation/              # Detailed guides
└── deployment/                 # Deployment scripts
```

## 🧪 Testing

### Quick Tests

```bash
# Run all tests
./deployment/run.sh test

# Test specific integration
python tests/test_notion_sync.py
python tests/test_todoist.py

# Run with pytest
python -m pytest tests/ -v
```

### Manual Testing

```bash
# Test Notion connection
python -c "from notion_integration import NotionIntegration; n = NotionIntegration(); print('✅ Connected!' if n.enabled else '❌ Failed')"

# Test Todoist connection
python -c "from todoist_integration import TodoistIntegration; t = TodoistIntegration(); print('✅ Connected!' if t.enabled else '❌ Failed')"
```

## 🔍 Troubleshooting

### Common Issues

#### Moodle Connection Problems

```bash
# Clear stored session data
python run_fetcher.py --clear-moodle-session

# Check with debug mode
python run_fetcher.py --test --debug
```

#### Notion Sync Issues

1. Verify your database schema matches requirements
2. Check that the integration has access to your database
3. Ensure your `NOTION_TOKEN` and `NOTION_DATABASE_ID` are correct

#### Todoist Sync Issues

1. Verify your `TODOIST_API_TOKEN` is valid
2. Check that the "Assignments" project exists
3. Ensure your account has API access enabled

### Debug Mode

```bash
# Enable maximum detail logging
python run_fetcher.py --debug

# Check logs
tail -f logs/moodle_fetcher.log
```

## 📚 Documentation

- **[Notion Integration Guide](documentation/notion-guide.md)** - Complete Notion setup and usage
- **[Todoist Integration Guide](documentation/todoist-guide.md)** - Todoist configuration and features
- **[Testing Guide](documentation/testing-guide.md)** - Comprehensive testing instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in `logs/moodle_fetcher.log`
3. Run with `--debug` flag for detailed information
4. Check the documentation in the `documentation/` folder

## 🔄 Changelog

### Recent Changes
- Removed `--skip-notion` and `--skip-todoist` flags for cleaner interface
- Enhanced direct Moodle scraping capabilities
- Improved error handling and logging
- Added comprehensive archive management system

---

**Happy Assignment Management! 🎓✨**
