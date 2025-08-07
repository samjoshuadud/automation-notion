# 🎯 Todoist Integration Guide

Complete guide for setting up, configuring, and using the Todoist integration in your Moodle Assignment Automation System.

## 📋 Table of Contents
- [Overview](#-overview)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Features](#-features)
- [Troubleshooting](#-troubleshooting)
- [Advanced Configuration](#-advanced-configuration)

---

## 🌟 Overview

The Todoist integration automatically converts your Moodle assignments into tasks in your Todoist workspace. It provides:

- **Automatic Task Creation**: Assignments become tasks with proper formatting
- **Smart Reminders**: Intelligent reminder scheduling based on due dates
- **Duplicate Prevention**: Prevents creating duplicate tasks
- **Bidirectional Sync**: Status updates sync between systems
- **Course Organization**: Tasks are labeled by course codes
- **Free Tier Compatible**: Works with Todoist's free plan

## ✅ Prerequisites

### Required
- **Todoist Account** (free or premium)
- **Python Environment** (3.8+)
- **Internet Connection** for API access

### Recommended
- **Todoist Mobile App** for on-the-go access
- **Basic familiarity** with Todoist interface

## 🚀 Setup Instructions

### Step 1: Get Your Todoist API Token

1. **Login to Todoist Web**
   - Go to [todoist.com](https://todoist.com)
   - Login to your account

2. **Access Integrations Settings**
   - Go to [Settings > Integrations](https://todoist.com/prefs/integrations)
   - Or click your profile picture → Settings → Integrations

3. **Find Your API Token**
   - Look for the "API token" section
   - Copy the long token string (starts with letters/numbers)
   - **Keep this secure** - it's like a password

### Step 2: Configure Environment Variables

1. **Edit your .env file**
   ```bash
   nano .env
   ```

2. **Add Todoist configuration**
   ```env
   # Todoist Integration
   TODOIST_TOKEN=your_api_token_here
   ```

3. **Save and close the file**
   ```bash
   # Press Ctrl+X, then Y, then Enter in nano
   ```

### Step 3: Test the Integration

1. **Run the setup script**
   ```bash
   /home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_todoist.py
   ```

2. **Expected output**
   ```
   🎯 TODOIST INTEGRATION SETUP
   ==================================================
   ✅ Todoist token found in .env file
   ✅ Todoist integration initialized
   ✅ Todoist API connection successful
   ✅ 'School Assignments' project ready
   🎉 TODOIST INTEGRATION SETUP COMPLETE!
   ```

## ⚙️ Configuration

### Basic Configuration

The integration works out-of-the-box with these defaults:

- **Project Name**: "School Assignments"
- **Task Priority**: Normal (level 2)
- **Reminder Logic**: Smart reminders based on due date
- **Labels**: Course codes (e.g., HCI, MATH, PROG)

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TODOIST_TOKEN` | Yes | Your Todoist API token | `abc123def456...` |

### Project Structure in Todoist

```
📋 School Assignments (Project)
├── 🏷️ HCI - Activity 1 (User Story)     [HCI]
├── 🏷️ MATH - Problem Set 3              [MATH]
├── 🏷️ PROG - Final Project Milestone    [PROG]
└── 🏷️ ENG - Essay Draft                 [ENG]
```

## 🎯 Usage

### Basic Operations

#### Sync Assignments to Todoist
```bash
# Fetch emails and sync to Todoist only
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist

# Sync to both Todoist and Notion
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist --notion
```

#### Test Mode (No Email Fetching)
```bash
# Test with existing data
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --test --todoist
```

#### Check Current Status
```bash
# Quick health check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py
```

## 🌟 Features

### Smart Task Formatting

**Input Assignment:**
```
Course: Human Computer Interaction
Title: ACTIVITY 1 - USER STORY [1]
Due: 2025-08-15
```

**Todoist Task:**
```
📋 Title: HCI - Activity 1 (User Story)
📅 Due: August 8, 2025 (reminder set for August 11)
🏷️ Labels: [hci]
📝 Description:
    📅 Deadline: August 15, 2025
    📚 Course: Human Computer Interaction
    📧 Source: Moodle Email
    🔗 Email ID: abc123
```

### Smart Reminder System

The system calculates optimal reminder dates:

| Days Until Due | Reminder Schedule |
|----------------|-------------------|
| 1-3 days | 1 day before (or today if due tomorrow) |
| 4-7 days | 3 days before |
| 8-14 days | 5 days before |
| 15-30 days | 1 week before |
| 30+ days | 2 weeks before |

### Duplicate Prevention

The system prevents duplicates using:
1. **Email ID matching** (most reliable)
2. **Normalized title comparison**
3. **Fuzzy matching** for similar assignments

### Bidirectional Status Sync

- Mark task complete in Todoist → Updates local status
- Mark assignment complete locally → Updates Todoist
- Automatic sync during each run

## 🔧 Troubleshooting

### Common Issues

#### "Todoist integration not enabled"
**Cause**: Missing or invalid API token
**Solution**:
```bash
# Check token configuration
grep TODOIST_TOKEN .env

# If missing, add it:
echo "TODOIST_TOKEN=your_token_here" >> .env
```

#### "Connection failed"
**Cause**: Network or authentication issue
**Solution**:
```bash
# Test connection manually
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import requests
headers = {'Authorization': 'Bearer YOUR_TOKEN_HERE'}
response = requests.get('https://api.todoist.com/rest/v2/projects', headers=headers)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:100]}')
"
```

#### "No tasks created"
**Cause**: No new assignments or all are duplicates
**Solution**:
```bash
# Check for existing tasks
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
todoist = TodoistIntegration()
tasks = todoist.get_all_assignments_from_todoist()
print(f'Found {len(tasks)} existing tasks')
"
```

## 📱 Mobile Usage

### Todoist Mobile App

1. **Download the app**
   - iOS: App Store
   - Android: Google Play Store

2. **Login with same account**
   - Use same credentials as web version

3. **Access your assignments**
   - Look for "School Assignments" project
   - All tasks sync automatically

### Mobile Workflow

1. **View assignments** in Todoist mobile app
2. **Mark complete** when finished
3. **Status syncs** back to local system
4. **Archived automatically** after 30 days

## 🔄 Automation

### Daily Sync (Recommended)

Add to crontab for automatic daily sync:
```bash
# Edit crontab
crontab -e

# Add this line for daily sync at 8 AM
0 8 * * * cd /home/punisher/Documents/automate && /home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist
```

### Multiple Daily Syncs

For more frequent updates:
```bash
# Every 4 hours during day (8 AM, 12 PM, 4 PM, 8 PM)
0 8,12,16,20 * * * cd /home/punisher/Documents/automate && /home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist
```

## 📊 Monitoring

### Health Checks

Regular monitoring commands:
```bash
# Daily health check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py

# Weekly statistics
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
todoist = TodoistIntegration()
stats = todoist.get_project_stats()
print('Weekly Report:')
print(f'  Total tasks: {stats.get(\"total_tasks\", 0)}')
print(f'  Completed this week: {stats.get(\"completed_tasks\", 0)}')
print(f'  Overdue: {stats.get(\"overdue_tasks\", 0)}')
"
```

### Performance Metrics

Track system performance:
```bash
# Monitor sync time
time /home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --test --todoist

# Check memory usage during sync
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import psutil, time
from todoist_integration import TodoistIntegration

start_memory = psutil.Process().memory_info().rss / 1024 / 1024
start_time = time.time()

todoist = TodoistIntegration()
tasks = todoist.get_all_assignments_from_todoist()

end_time = time.time()
end_memory = psutil.Process().memory_info().rss / 1024 / 1024

print(f'Loaded {len(tasks)} tasks in {end_time - start_time:.2f}s')
print(f'Memory: {end_memory:.1f}MB (+{end_memory - start_memory:.1f}MB)')
"
```

## 🆘 Support

### Getting Help

1. **Check logs**: Look in `logs/moodle_fetcher.log`
2. **Run diagnostics**: Use troubleshooting commands above
3. **Test components**: Use individual test scripts
4. **Check documentation**: Review other guides in this folder

### Useful Commands Reference

```bash
# Quick health check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py

# Full test suite
/home/punisher/Documents/automate/vehicle-python/bin/python tests/run_all_tests.py

# Setup and configuration
/home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_todoist.py

# Debug connection
/home/punisher/Documents/automate/vehicle-python/bin/python -c "from todoist_integration import TodoistIntegration; print('✅ OK' if TodoistIntegration()._test_connection() else '❌ FAILED')"
```

---

**Last Updated**: August 7, 2025  
**Todoist API Version**: v2  
**Compatibility**: Free and Premium Todoist accounts
