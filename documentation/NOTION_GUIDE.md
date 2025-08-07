# 📝 Notion Integration Guide

Complete guide for setting up, configuring, and using the Notion integration in your Moodle Assignment Automation System.

## 📋 Table of Contents
- [Overview](#-overview)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
- [Database Configuration](#-database-configuration)
- [Usage](#-usage)
- [Features](#-features)
- [Troubleshooting](#-troubleshooting)
- [Advanced Configuration](#-advanced-configuration)

---

## 🌟 Overview

The Notion integration creates a comprehensive assignment management database in your Notion workspace. It provides:

- **Structured Database**: Professional assignment tracking with rich properties
- **Automatic Sync**: Bidirectional synchronization with local data
- **Status Management**: Complete lifecycle tracking from creation to archive
- **Rich Formatting**: Course information, due dates, and detailed descriptions
- **Archive System**: Intelligent archiving of completed assignments
- **Search & Filter**: Powerful Notion database capabilities

## ✅ Prerequisites

### Required
- **Notion Account** (free or paid)
- **Notion Integration** (we'll create this)
- **Python Environment** (3.8+)
- **Internet Connection** for API access

### Recommended
- **Notion Desktop/Mobile App** for best experience
- **Basic familiarity** with Notion databases
- **Understanding of Notion properties** and views

## 🚀 Setup Instructions

### Step 1: Create Notion Integration

1. **Go to Notion Integrations**
   - Visit [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click "New integration"

2. **Configure Integration**
   - **Name**: "Moodle Assignment Automation"
   - **Logo**: Upload a logo (optional)
   - **Associated workspace**: Select your workspace
   - **Capabilities**: Leave default (Read content, Update content, Insert content)

3. **Get Integration Token**
   - After creation, copy the "Internal Integration Token"
   - It starts with `secret_` and is about 50 characters long
   - **Keep this secure** - treat it like a password

### Step 2: Create Assignment Database

1. **Create New Database**
   - In Notion, create a new page
   - Add a database (full page)
   - Name it "Assignment Tracker" or similar

2. **Share Database with Integration**
   - Click "Share" in top-right
   - Click "Invite"
   - Search for your integration name ("Moodle Assignment Automation")
   - Click "Invite"

3. **Get Database ID**
   - Copy the database URL
   - Extract the ID (32-character string between last `/` and `?`)
   - Example: `https://notion.so/abc123def456?v=...`
   - Database ID is: `abc123def456`

### Step 3: Configure Environment Variables

1. **Edit your .env file**
   ```bash
   nano .env
   ```

2. **Add Notion configuration**
   ```env
   # Notion Integration
   NOTION_TOKEN=secret_abc123def456...
   NOTION_DATABASE_ID=your_database_id_here
   ```

3. **Save and close the file**

### Step 4: Set Up Database Properties

1. **Run the setup script**
   ```bash
   /home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_notion_db.py
   ```

2. **Expected output**
   ```
   🔧 NOTION DATABASE SETUP
   ========================
   ✅ Connected to Notion
   ✅ Database found and accessible
   ✅ All required properties created
   📊 Database is ready for assignments!
   ```

### Step 5: Test the Integration

1. **Run integration test**
   ```bash
   /home/punisher/Documents/automate/vehicle-python/bin/python tests/test_notion_sync.py
   ```

2. **Expected result**
   ```
   🧪 NOTION INTEGRATION TEST
   ==========================
   ✅ Connection successful
   ✅ Database accessible
   ✅ Test assignment created
   ✅ Test assignment retrieved
   ✅ All tests passed!
   ```

## 🗄️ Database Configuration

### Required Properties

The setup script creates these essential properties:

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| **Title** | Title | Assignment name | HCI - Activity 1 (User Story) |
| **Course** | Select | Course name | Human Computer Interaction |
| **Course Code** | Select | Short course identifier | HCI |
| **Due Date** | Date | Assignment deadline | 2025-08-15 |
| **Status** | Select | Current status | Pending, In Progress, Completed |
| **Email ID** | Rich Text | Unique identifier | abc123def456 |
| **Source** | Select | Where assignment came from | Moodle Email |
| **Priority** | Select | Assignment priority | High, Medium, Low |
| **Description** | Rich Text | Assignment details | Full assignment description |
| **Last Updated** | Date | When last modified | 2025-08-07 |

### Status Options

The Status property includes these options:

- 🆕 **Pending** - New assignment, not started
- ⏳ **In Progress** - Currently working on it
- ✅ **Completed** - Finished assignment
- 📥 **Submitted** - Turned in to instructor
- 📚 **Archived** - Old, completed assignment

### Course Code Options

Automatically populated based on your assignments:

- 🎨 **HCI** - Human Computer Interaction
- 🧮 **MATH** - Mathematics courses
- 💻 **PROG** - Programming courses
- 📖 **ENG** - English courses
- 🔬 **SCI** - Science courses

## 🎯 Usage

### Basic Operations

#### Sync Assignments to Notion
```bash
# Fetch emails and sync to Notion only
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --notion

# Sync to both Notion and Todoist
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --notion --todoist
```

#### Test Mode (No Email Fetching)
```bash
# Test with existing data
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --test --notion
```

#### Check Current Status
```bash
# Quick health check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py
```

### Advanced Operations

#### Manual Database Check
```bash
# Check database properties
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from notion_integration import NotionIntegration
notion = NotionIntegration()
if notion.enabled:
    print('✅ Notion integration working')
    # Add any specific checks here
else:
    print('❌ Notion not enabled')
"
```

#### View Database Statistics
```bash
# Get assignment statistics
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from notion_integration import NotionIntegration
import json

notion = NotionIntegration()
if notion.enabled:
    # This would require implementing get_database_stats method
    print('Database statistics would appear here')
else:
    print('❌ Notion not enabled')
"
```

## 🌟 Features

### Assignment Formatting

**Input Assignment:**
```
Course: Human Computer Interaction
Title: ACTIVITY 1 - USER STORY [1]
Due: 2025-08-15
Email ID: abc123def456
```

**Notion Database Entry:**
```
📝 Title: HCI - Activity 1 (User Story)
📚 Course: Human Computer Interaction
🏷️ Course Code: HCI
📅 Due Date: August 15, 2025
📊 Status: Pending
🔗 Email ID: abc123def456
📧 Source: Moodle Email
⭐ Priority: Medium
📄 Description: Full assignment details...
🕒 Last Updated: August 7, 2025
```

### Bidirectional Sync

- **Local to Notion**: New assignments create database entries
- **Notion to Local**: Status changes sync back to local storage
- **Archive Integration**: Completed assignments are archived after 30 days

### Smart Duplicate Prevention

Prevents duplicate entries using:
1. **Email ID matching** (primary method)
2. **Title and course combination**
3. **Date and content similarity**

### Rich Database Views

Create custom views in Notion:

- **📅 By Due Date**: Sorted by upcoming deadlines
- **📚 By Course**: Grouped by course/subject
- **📊 By Status**: Filter by completion status
- **⭐ By Priority**: Show high-priority assignments first
- **📈 Progress Board**: Kanban-style status board

## 🔧 Troubleshooting

### Common Issues

#### "Notion integration not enabled"
**Cause**: Missing token or database ID
**Solution**:
```bash
# Check configuration
grep -E "(NOTION_TOKEN|NOTION_DATABASE_ID)" .env

# If missing, add them:
echo "NOTION_TOKEN=secret_your_token_here" >> .env
echo "NOTION_DATABASE_ID=your_database_id" >> .env
```

#### "Database not found"
**Cause**: Database not shared with integration
**Solution**:
1. Go to your Notion database
2. Click "Share" in top-right
3. Search for your integration name
4. Click "Invite" to share access

#### "Invalid database ID"
**Cause**: Wrong database ID format
**Solution**:
```bash
# Database ID should be 32 characters, like:
# abc123def456789012345678901234567890
# Extract from URL: https://notion.so/DATABASE_ID?v=...
```

#### "Properties not found"
**Cause**: Database properties not set up correctly
**Solution**:
```bash
# Re-run the setup script
/home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_notion_db.py
```

### Debug Mode

Enable detailed logging:
```bash
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from notion_integration import NotionIntegration
notion = NotionIntegration()
# All operations will show detailed logs
"
```

### Connection Testing

Test Notion API connection:
```bash
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import requests

token = 'YOUR_NOTION_TOKEN'
headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.notion.com/v1/users/me', headers=headers)
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:100]}')
"
```

## 🎛️ Advanced Configuration

### Custom Database Properties

Add additional properties to track more information:

1. **In Notion Database**:
   - Add new property (e.g., "Estimated Hours")
   - Set appropriate type (Number, Select, etc.)

2. **Update Integration Code**:
   ```python
   # In notion_integration.py, modify the create/update methods
   # to include your custom properties
   ```

### Multiple Databases

Set up separate databases for different purposes:

```bash
# Create separate databases for:
# - Current assignments (active work)
# - Completed assignments (historical record)
# - Course planning (future assignments)
```

### Advanced Views

Create sophisticated Notion views:

#### 📅 **Timeline View**
- Group by: Due Date
- Sort: Due Date (ascending)
- Filter: Status ≠ Completed

#### 📊 **Status Board**
- Group by: Status
- Show as: Board
- Sort: Priority, Due Date

#### 📚 **Course Overview**
- Group by: Course
- Sort: Due Date
- Properties: Title, Due Date, Status

#### 🎯 **Priority Dashboard**
- Filter: Priority = High OR Due Date ≤ 7 days
- Sort: Due Date (ascending)
- Properties: Title, Course, Due Date, Status

## 📱 Mobile Usage

### Notion Mobile App

1. **Download Notion app**
   - iOS: App Store
   - Android: Google Play Store

2. **Access your database**
   - Login with same account
   - Navigate to your Assignment Tracker database

3. **Mobile workflow**
   - View assignments on-the-go
   - Update status while working
   - Add notes and comments
   - Get push notifications

### Offline Access

- **Notion Mobile**: Limited offline access
- **Sync**: Changes sync when back online
- **Backup**: Always maintain local data backups

## 🔄 Automation

### Automatic Sync Schedule

Set up regular synchronization:

```bash
# Edit crontab
crontab -e

# Add daily sync at 8 AM
0 8 * * * cd /home/punisher/Documents/automate && /home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --notion

# Add evening status sync at 8 PM
0 20 * * * cd /home/punisher/Documents/automate && /home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --notion --test
```

### Archive Automation

Completed assignments are automatically archived:
- **Trigger**: Status = "Completed" for 30+ days
- **Action**: Moved to archive database or local storage
- **Restore**: Can be restored if status changes

## 📊 Analytics and Reporting

### Database Insights

Create analytical views in Notion:

#### 📈 **Completion Rate**
- Formula property: Completed / Total assignments
- Rollup by course or time period

#### ⏱️ **Average Completion Time**
- Track from creation to completion
- Group by course difficulty

#### 📅 **Due Date Analysis**
- Identify scheduling patterns
- Optimize workload distribution

### Export Options

Extract data for external analysis:
```bash
# Export assignments to CSV (requires additional implementation)
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import json
import csv

with open('data/assignments.json', 'r') as f:
    assignments = json.load(f)

with open('assignments_export.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'course', 'due_date', 'status'])
    writer.writeheader()
    for assignment in assignments:
        writer.writerow({
            'title': assignment.get('title', ''),
            'course': assignment.get('course', ''),
            'due_date': assignment.get('due_date', ''),
            'status': assignment.get('status', '')
        })

print('✅ Exported to assignments_export.csv')
"
```

## 🆘 Support

### Getting Help

1. **Check logs**: Look in `logs/moodle_fetcher.log`
2. **Run diagnostics**: Use troubleshooting commands above
3. **Test database**: Use `tests/setup_notion_db.py`
4. **Check Notion status**: Visit [Notion Status Page](https://status.notion.so/)

### Useful Commands Reference

```bash
# Quick health check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py

# Database setup
/home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_notion_db.py

# Full test suite
/home/punisher/Documents/automate/vehicle-python/bin/python tests/run_all_tests.py

# Notion-specific tests
/home/punisher/Documents/automate/vehicle-python/bin/python tests/test_notion_sync.py
```

### Best Practices

1. **Regular Backups**: Export your database periodically
2. **Clean Organization**: Use consistent naming and tagging
3. **View Optimization**: Create views that match your workflow
4. **Property Standards**: Maintain consistent data entry
5. **Archive Management**: Review and clean old assignments

---

**Last Updated**: August 7, 2025  
**Notion API Version**: 2022-06-28  
**Compatibility**: All Notion plan types
