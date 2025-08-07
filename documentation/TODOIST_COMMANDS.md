# 🎯 Todoist Integration Commands Guide

This guide provides all the commands you need to test, use, and troubleshoot the Todoist integration in your Moodle Assignment Automation system.

## 📋 Table of Contents
- [Setup Commands](#-setup-commands)
- [Testing Commands](#-testing-commands)
- [Real-Time Usage Commands](#-real-time-usage-commands)
- [Duplicate Detection Testing](#-duplicate-detection-testing)
- [Troubleshooting Commands](#-troubleshooting-commands)
- [Advanced Usage](#-advanced-usage)
- [Monitoring Commands](#-monitoring-commands)

---

## 🛠️ Setup Commands

### Initial Setup
```bash
# Set up Todoist integration (interactive setup)
/home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_todoist.py

# Quick connection test
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
t = TodoistIntegration()
print('✅ Connected' if t.enabled and t._test_connection() else '❌ Failed')
"
```

### Environment Check
```bash
# Check if Todoist token is configured
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TODOIST_TOKEN')
print('✅ Token configured' if token else '❌ No token found')
"
```

---

## 🧪 Testing Commands

### Basic Functionality Tests
```bash
# Run comprehensive Todoist test suite
/home/punisher/Documents/automate/vehicle-python/bin/python tests/test_todoist_sync.py

# Run all tests (Todoist + Notion)
/home/punisher/Documents/automate/vehicle-python/bin/python tests/run_all_tests.py

# Quick integration check
/home/punisher/Documents/automate/vehicle-python/bin/python tests/quick_integration_check.py
```

### Connection Testing
```bash
# Test API connection only
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    result = todoist._test_connection()
    print(f'Connection: {\"✅ Success\" if result else \"❌ Failed\"}')
else:
    print('❌ Todoist not enabled')
"
```

### Project Testing
```bash
# Test project creation/retrieval
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    project_id = todoist.get_or_create_project('School Assignments')
    print(f'Project ID: {project_id}')
    
    stats = todoist.get_project_stats()
    print(f'Stats: {stats}')
else:
    print('❌ Todoist not enabled')
"
```

---

## 🚀 Real-Time Usage Commands

### Basic Syncing
```bash
# Fetch emails and sync to Todoist only
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist

# Fetch emails and sync to both Todoist and Notion
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --todoist --notion

# Test mode (no actual email fetching, uses cached data)
/home/punisher/Documents/automate/vehicle-python/bin/python run_fetcher.py --test --todoist
```

### Manual Task Creation
```bash
# Create a test assignment task
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

todoist = TodoistIntegration()
if todoist.enabled:
    test_assignment = {
        'title': 'SAMPLE - Activity 1 (Manual Test)',
        'title_normalized': 'sample - activity 1 (manual test)',
        'course_code': 'SAMPLE',
        'due_date': '2025-08-20',
        'email_id': 'manual_test_' + str(int(__import__('time').time())),
        'course': 'Sample Course for Testing',
        'source': 'Manual Command Test',
        'raw_title': 'ACTIVITY 1 - MANUAL TEST [1]'
    }
    
    success = todoist.create_assignment_task(test_assignment)
    print(f'Task creation: {\"✅ Success\" if success else \"❌ Failed\"}')
else:
    print('❌ Todoist not enabled')
"
```

### Get Current Tasks
```bash
# List all current assignments in Todoist
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    tasks = todoist.get_all_assignments_from_todoist()
    print(f'📋 Found {len(tasks)} tasks:')
    for i, task in enumerate(tasks[:10], 1):
        status = '✅' if task['completed'] else '⏳'
        print(f'  {i}. {status} {task[\"title\"][:60]}...')
    if len(tasks) > 10:
        print(f'  ... and {len(tasks) - 10} more tasks')
else:
    print('❌ Todoist not enabled')
"
```

---

## 🔍 Duplicate Detection Testing

### Test Duplicate Detection
```bash
# Run focused duplicate detection test
/home/punisher/Documents/automate/vehicle-python/bin/python test_duplicate_detection.py

# Manual duplicate check
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

todoist = TodoistIntegration()
if todoist.enabled:
    # Get first existing task
    tasks = todoist.get_all_assignments_from_todoist()
    if tasks:
        existing_task = tasks[0]
        print(f'Testing duplicate detection with: {existing_task[\"title\"][:50]}...')
        
        # Create similar assignment
        test_assignment = {
            'title': existing_task['title'],
            'title_normalized': existing_task['title'].lower(),
            'email_id': existing_task.get('email_id', 'test_123'),
            'course_code': 'TEST'
        }
        
        duplicate_id = todoist.task_exists_in_todoist(test_assignment)
        print(f'Duplicate check result: {\"✅ Found (\" + duplicate_id + \")\" if duplicate_id else \"❌ Not found\"}')
    else:
        print('No existing tasks to test with')
else:
    print('❌ Todoist not enabled')
"
```

### Test Sync with Duplicates
```bash
# Test sync process with duplicate filtering
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

todoist = TodoistIntegration()
if todoist.enabled:
    # Create test assignments (some may be duplicates)
    test_assignments = [
        {
            'title': 'TEST1 - Activity 1 (Sync Test)',
            'title_normalized': 'test1 - activity 1 (sync test)',
            'course_code': 'TEST1',
            'due_date': '2025-08-25',
            'email_id': 'sync_test_1',
            'course': 'Test Course 1',
            'source': 'Sync Test'
        },
        {
            'title': 'TEST2 - Activity 2 (Sync Test)',
            'title_normalized': 'test2 - activity 2 (sync test)',
            'course_code': 'TEST2',
            'due_date': '2025-08-26',
            'email_id': 'sync_test_2',
            'course': 'Test Course 2',
            'source': 'Sync Test'
        }
    ]
    
    print(f'Syncing {len(test_assignments)} test assignments...')
    synced_count = todoist.sync_assignments(test_assignments)
    print(f'Synced: {synced_count} new assignments')
    
    # Try syncing the same assignments again (should detect duplicates)
    print('\\nTrying to sync the same assignments again...')
    synced_count2 = todoist.sync_assignments(test_assignments)
    print(f'Synced on second attempt: {synced_count2} (should be 0 if duplicate detection works)')
else:
    print('❌ Todoist not enabled')
"
```

---

## 🔧 Troubleshooting Commands

### Debug Connection Issues
```bash
# Verbose connection test
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import requests
import os
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
token = os.getenv('TODOIST_TOKEN')

if not token:
    print('❌ No TODOIST_TOKEN found in .env file')
    exit(1)

print(f'Token length: {len(token)} characters')
print(f'Token starts with: {token[:10]}...')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
url = 'https://api.todoist.com/rest/v2/projects'

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text[:200]}...')
    
    if response.status_code == 200:
        projects = response.json()
        print(f'✅ Found {len(projects)} projects')
    else:
        print(f'❌ API Error: {response.status_code}')
except Exception as e:
    print(f'❌ Request failed: {e}')
"
```

### Check Environment Variables
```bash
# Check all environment variables
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import os
from dotenv import load_dotenv

load_dotenv()

env_vars = [
    'TODOIST_TOKEN',
    'GMAIL_EMAIL', 
    'GMAIL_APP_PASSWORD',
    'NOTION_TOKEN',
    'NOTION_DATABASE_ID'
]

print('Environment Variables Status:')
for var in env_vars:
    value = os.getenv(var)
    if value:
        masked = value[:5] + '*' * (len(value) - 5) if len(value) > 5 else '*' * len(value)
        print(f'  ✅ {var}: {masked}')
    else:
        print(f'  ❌ {var}: Not set')
"
```

### Debug Logging
```bash
# Enable debug logging for detailed output
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from todoist_integration import TodoistIntegration

todoist = TodoistIntegration()
print('Check the detailed logs above for any issues')
"
```

---

## 🎯 Advanced Usage

### Batch Operations
```bash
# Sync specific assignments from JSON file
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import json
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    try:
        with open('data/assignments.json', 'r') as f:
            assignments = json.load(f)
        
        print(f'Found {len(assignments)} assignments in local data')
        synced = todoist.sync_assignments(assignments)
        print(f'Synced {synced} new assignments to Todoist')
    except FileNotFoundError:
        print('❌ No assignments.json found. Run email fetcher first.')
    except Exception as e:
        print(f'❌ Error: {e}')
else:
    print('❌ Todoist not enabled')
"
```

### Status Synchronization
```bash
# Sync completion status from Todoist back to local storage
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import json
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    try:
        with open('data/assignments.json', 'r') as f:
            local_assignments = json.load(f)
        
        result = todoist.sync_status_from_todoist(local_assignments)
        print(f'Updated {result[\"updated\"]} assignments from Todoist')
        
        if result['completed_in_todoist']:
            print('Completed assignments:')
            for title in result['completed_in_todoist']:
                print(f'  ✅ {title}')
    except FileNotFoundError:
        print('❌ No local assignments found')
    except Exception as e:
        print(f'❌ Error: {e}')
else:
    print('❌ Todoist not enabled')
"
```

### Clean Up Test Tasks
```bash
# Remove test tasks (be careful with this!)
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    tasks = todoist.get_all_assignments_from_todoist()
    test_tasks = [t for t in tasks if 'TEST' in t['title'].upper() or 'SAMPLE' in t['title'].upper()]
    
    print(f'Found {len(test_tasks)} test tasks')
    for task in test_tasks:
        print(f'  - {task[\"title\"]}')
    
    if test_tasks:
        confirm = input('\\nDelete these test tasks? (y/N): ').strip().lower()
        if confirm == 'y':
            for task in test_tasks:
                success = todoist.delete_task(task['id'])
                print(f'  {\"✅\" if success else \"❌\"} {task[\"title\"]}')
        else:
            print('Cancelled')
    else:
        print('No test tasks found')
else:
    print('❌ Todoist not enabled')
"
```

---

## 📊 Monitoring Commands

### Get Project Statistics
```bash
# Show detailed project statistics
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    stats = todoist.get_project_stats()
    
    print('📊 SCHOOL ASSIGNMENTS PROJECT STATS')
    print('=' * 40)
    print(f'Total tasks: {stats.get(\"total_tasks\", 0)}')
    print(f'Completed: {stats.get(\"completed_tasks\", 0)}')
    print(f'Pending: {stats.get(\"pending_tasks\", 0)}')
    print(f'Overdue: {stats.get(\"overdue_tasks\", 0)}')
    print(f'Due today: {stats.get(\"due_today\", 0)}')
    print(f'Due this week: {stats.get(\"due_this_week\", 0)}')
    
    if stats.get('total_tasks', 0) > 0:
        completion_rate = (stats.get('completed_tasks', 0) / stats.get('total_tasks', 1)) * 100
        print(f'Completion rate: {completion_rate:.1f}%')
else:
    print('❌ Todoist not enabled')
"
```

### Monitor Recent Activity
```bash
# Show recent tasks and their status
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
from todoist_integration import TodoistIntegration
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)

todoist = TodoistIntegration()
if todoist.enabled:
    tasks = todoist.get_all_assignments_from_todoist()
    
    # Sort by creation date (most recent first)
    recent_tasks = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    
    print('📋 RECENT TASKS (Last 10)')
    print('=' * 50)
    for i, task in enumerate(recent_tasks, 1):
        status = '✅' if task['completed'] else '⏳'
        due = task.get('due_date', 'No due date')
        print(f'{i:2}. {status} {task[\"title\"][:45]}...')
        print(f'    Due: {due}')
        if task.get('labels'):
            print(f'    Labels: {task[\"labels\"]}')
        print()
else:
    print('❌ Todoist not enabled')
"
```

---

## 🚨 Emergency Commands

### Force Sync All
```bash
# Force sync all assignments (ignoring duplicates)
/home/punisher/Documents/automate/vehicle-python/bin/python -c "
import json
from todoist_integration import TodoistIntegration
import logging
logging.basicConfig(level=logging.INFO)

print('⚠️  FORCE SYNC - This may create duplicates!')
confirm = input('Continue? (y/N): ').strip().lower()

if confirm == 'y':
    todoist = TodoistIntegration()
    if todoist.enabled:
        try:
            with open('data/assignments.json', 'r') as f:
                assignments = json.load(f)
            
            for assignment in assignments:
                success = todoist.create_assignment_task(assignment)
                print(f'{\"✅\" if success else \"❌\"} {assignment.get(\"title\", \"Unknown\")}')
        except Exception as e:
            print(f'❌ Error: {e}')
    else:
        print('❌ Todoist not enabled')
else:
    print('Cancelled')
"
```

### Reset Integration
```bash
# Reset Todoist integration (clear all assignment tasks)
echo "⚠️  WARNING: This will delete ALL tasks in 'School Assignments' project!"
echo "Use the Todoist web interface to manually delete the project if needed."
echo "Then run: /home/punisher/Documents/automate/vehicle-python/bin/python tests/setup_todoist.py"
```

---

## 💡 Usage Tips

1. **Always test first**: Use `--test` flag before real operations
2. **Check logs**: Enable INFO logging to see what's happening
3. **Monitor duplicates**: The system automatically prevents duplicates
4. **Regular sync**: Run fetcher daily to keep assignments updated
5. **Backup data**: Keep `data/assignments.json` backed up

## 🔗 Related Files

- `todoist_integration.py` - Main integration code
- `tests/test_todoist_sync.py` - Comprehensive test suite
- `tests/setup_todoist.py` - Interactive setup guide
- `run_fetcher.py` - Main application entry point
- `.env` - Environment variables configuration

---

**Last Updated**: August 7, 2025
**Python Environment**: `/home/punisher/Documents/automate/vehicle-python/bin/python`
