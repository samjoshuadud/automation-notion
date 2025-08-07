# 🎯 Todoist Integration Quick Start

A simple guide to get your Moodle assignments syncing to Todoist in under 5 minutes.

## ✨ Why Todoist?

- **✅ Free Tier Friendly**: Full functionality with free Todoist account
- **📱 Excellent Mobile App**: Best-in-class mobile experience
- **🔔 Smart Notifications**: Never miss a due date
- **⚡ Quick Setup**: Just need your API token
- **🌍 Cross-Platform**: Works everywhere - phone, tablet, computer, web

## 🚀 5-Minute Setup

### 1. Get Your Todoist API Token
1. Go to https://todoist.com/prefs/integrations
2. Find "API token" section
3. Copy your token (long string like `abc123def456...`)

### 2. Add Token to Your System
```bash
# Edit your .env file
nano .env

# Add this line:
TODOIST_TOKEN=your_api_token_here
```

### 3. Test the Connection
```bash
python tests/setup_todoist.py
```

### 4. Start Syncing!
```bash
# Fetch assignments and sync to Todoist
python run_fetcher.py --todoist
```

## 📋 What You'll Get in Todoist

### Project Structure
- **"School Assignments"** project automatically created
- All your assignments as individual tasks
- Due dates automatically set

### Task Format
```
HCI - Activity 1 (User Story)
Reminder: Aug 10, 2025 (Due: Aug 15, 2025)
Description: 📅 Deadline: August 15, 2025
             📚 Course: HCI - HUMAN COMPUTER INTERACTION
             🔗 Email ID: 756
```

### Smart Features
- **Intelligent Reminders**: Automatically calculated based on due date
  - 1-3 days away: Remind 1 day before
  - 4-7 days away: Remind 3 days before  
  - 8-14 days away: Remind 5 days before
  - 15-30 days away: Remind 1 week before
  - 30+ days away: Remind 2 weeks before
- **Status Sync**: Marking tasks complete in Todoist updates local storage
- **Duplicate Prevention**: Won't recreate tasks already completed

### Labels & Organization
- Course codes become labels: `#hci`, `#math`, etc.
- Easy filtering by subject
- Clean, organized task list

## 🔄 Daily Usage

### Basic Commands
```bash
# Check for new assignments
python run_fetcher.py --todoist

# With verbose logging (helpful for debugging)
python run_fetcher.py --todoist --verbose

# Test connection only
python run_fetcher.py --test --todoist
```

### Automation Options
```bash
# Every 2 hours during active hours (8am-6pm)
crontab -e
# Add: 0 8,10,12,14,16,18 * * * cd /path/to/automate && python run_fetcher.py --todoist
```

## 📱 Using Todoist

### Mobile App Features
- **Due Date Reminders**: Get notified before deadlines
- **Quick Entry**: Add notes and subtasks
- **Offline Sync**: Works without internet, syncs when connected
- **Widget Support**: See assignments on home screen

### Desktop/Web Features
- **Keyboard Shortcuts**: Quick task management
- **Project Views**: Filter by course/subject
- **Calendar Integration**: See due dates in calendar view
- **Statistics**: Track completion rates

## 🎯 Pro Tips

### Organization
1. **Use Labels**: Filter tasks by course using labels
2. **Set Priorities**: Mark urgent assignments with priority levels
3. **Add Subtasks**: Break down large assignments
4. **Use Comments**: Add notes and progress updates

### Workflow
1. **Morning Check**: Run `python run_fetcher.py --todoist`
2. **Review Tasks**: Check Todoist for today's assignments
3. **Mark Complete**: Check off finished assignments (syncs back to system!)
4. **Evening Planning**: Review tomorrow's tasks

### Status Synchronization
- ✅ **Bidirectional Sync**: Complete tasks in Todoist, status updates locally
- ✅ **Smart Prevention**: Won't recreate tasks already marked complete
- ✅ **Automatic Cleanup**: Completed tasks get archived after 30 days
- ✅ **Status Tracking**: Local database stays in sync with Todoist

### Free Tier Optimization
- **80 Projects**: More than enough for school organization
- **300 Tasks/Project**: Plenty for semester assignments
- **Basic Labels**: Organize by subject
- **Due Dates**: Never miss deadlines

## 🛠️ Troubleshooting

### Common Issues

**"Todoist integration not enabled"**
```bash
# Check your .env file has the token
cat .env | grep TODOIST_TOKEN

# Test the token
python tests/setup_todoist.py
```

**"No assignments found"**
```bash
# Check if you have local assignments
ls -la data/assignments.json

# Fetch new assignments first
python run_fetcher.py --days 14 --todoist
```

**"Connection failed"**
```bash
# Verify your API token at todoist.com/prefs/integrations
# Make sure token is correctly added to .env file
```

### Debug Commands
```bash
# Test Todoist integration specifically
python tests/test_todoist_sync.py

# Verbose logging to see what's happening
python tests/run_fetcher.py --todoist --verbose

# Test connection without fetching
python tests/run_fetcher.py --test --todoist

# Comprehensive bug testing
python tests/test_bug_detection.py

# Logic validation and loophole checking
python tests/test_logic_validation.py

# Stress testing for performance issues
python tests/test_stress.py

# Run all tests at once
python tests/run_all_tests.py
```

## 🧪 Testing & Quality Assurance

### Comprehensive Testing Suite
The system includes extensive tests to catch bugs and loopholes:

```bash
# Quick health check
python tests/run_all_tests.py --quick

# Full test suite (recommended before production)
python tests/run_all_tests.py

# Check prerequisites only
python tests/run_all_tests.py --prereq-only
```

### What Gets Tested
- ✅ **Edge Cases**: Invalid dates, empty data, malformed content
- ✅ **Duplicate Detection**: Prevents creating duplicate tasks
- ✅ **Status Sync**: Bidirectional synchronization logic
- ✅ **Performance**: Memory usage, API rate limits, large datasets
- ✅ **Error Handling**: Network failures, API errors, data corruption
- ✅ **Security**: Sensitive data exposure, input validation

### Common Test Scenarios
```bash
# Test with large datasets
python tests/test_stress.py

# Test edge cases and error conditions  
python tests/test_bug_detection.py

# Validate business logic
python tests/test_logic_validation.py

# Test status synchronization
python tests/test_status_sync.py
```

## 🌟 Advanced Features

### Sync with Both Systems
```bash
# Use both Notion and Todoist together
python run_fetcher.py --notion --todoist
```
- Notion for detailed project tracking
- Todoist for daily task management

### Custom Project Names
The system automatically creates a "School Assignments" project, but you can modify the project name in the Todoist integration code if needed.

### Batch Operations
```bash
# Sync last 30 days of assignments
python run_fetcher.py --days 30 --todoist

# Archive old completed assignments
python run_fetcher.py --cleanup --cleanup-days 30
```

## 📞 Support

If you run into issues:

1. **Check the main README.md** for detailed troubleshooting
2. **Run the test scripts** to isolate the problem
3. **Check logs** in `moodle_fetcher.log`
4. **Verify your API token** at Todoist integrations page

## 🎉 Success!

Once set up, you'll have:
- ✅ Automatic assignment detection from email
- ✅ Tasks created in Todoist with due dates
- ✅ Course-based organization with labels
- ✅ Cross-platform access to your assignments
- ✅ Smart notifications for due dates

**Enjoy your automated assignment management!** 🚀
