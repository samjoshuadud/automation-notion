# 🧪 Testing Guide & Commands

Complete guide for testing the Moodle Assignment Fetcher system with all available test commands and debugging tools.

## 🚀 Quick Start

```bash
# Run all basic tests
./deployment/run.sh test

# Run comprehensive test suite
python -m pytest tests/ -v

# Test specific integration
python tests/test_notion_stress.py
```

## 📋 Table of Contents

- [Test Overview](#-test-overview)
- [Basic Testing Commands](#-basic-testing-commands)
- [Integration Tests](#-integration-tests)
- [Stress & Performance Tests](#-stress--performance-tests)
- [Debugging Tools](#-debugging-tools)
- [Test Development](#-test-development)
- [Troubleshooting Tests](#-troubleshooting-tests)

## 🔍 Test Overview

### Test Categories

| Category | Purpose | Files | Duration |
|----------|---------|-------|----------|
| **Unit Tests** | Test individual functions | `test_parsing.py` | < 1 min |
| **Integration Tests** | Test system connections | `test_notion_sync.py` | 1-3 min |
| **Stress Tests** | Test performance limits | `test_notion_stress.py` | 5-10 min |
| **Real Data Tests** | Test with actual emails | `test_real_parsing.py` | 2-5 min |
| **Setup Tests** | Validate configuration | `setup_notion_db.py` | < 1 min |

### Test Structure

```
tests/
├── setup_notion_db.py      # Database setup & validation
├── test_notion_sync.py     # Notion integration tests
├── test_parsing.py         # Email parsing unit tests
├── test_real_parsing.py    # Real email data tests
└── test_notion_stress.py   # Performance & stress tests
```

## 🎯 Basic Testing Commands

### Quick System Test

```bash
# Test all integrations (Gmail, Notion, Todoist)
./deployment/run.sh test

# Test with verbose output
python run_fetcher.py --test --verbose
```

### Connection Tests

```bash
# Test Gmail connection only
python -c "
from moodle_fetcher import MoodleEmailFetcher
fetcher = MoodleEmailFetcher()
print('✅ Gmail connected' if fetcher.test_connection() else '❌ Gmail failed')
"

# Test Notion connection only
python -c "
from notion_integration import NotionIntegration
notion = NotionIntegration()
print('✅ Notion connected' if notion.enabled else '❌ Notion failed')
"

# Test Todoist connection only
python -c "
from todoist_integration import TodoistIntegration
todoist = TodoistIntegration()
print('✅ Todoist connected' if todoist.enabled else '❌ Todoist failed')
"
```

### Configuration Tests

```bash
# Validate environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['GMAIL_USER', 'GMAIL_PASSWORD']
optional_vars = ['NOTION_TOKEN', 'TODOIST_API_TOKEN']

for var in required_vars:
    status = '✅' if os.getenv(var) else '❌'
    print(f'{status} {var}: {\"Set\" if os.getenv(var) else \"Missing\"}')

for var in optional_vars:
    status = '✅' if os.getenv(var) else '⚠️'
    print(f'{status} {var}: {\"Set\" if os.getenv(var) else \"Not set\"}')
"

# Test .env file loading
python -c "
from dotenv import load_dotenv
load_dotenv()
print('✅ .env file loaded successfully')
"
```

## 🔗 Integration Tests

### Notion Integration Tests

```bash
# Basic Notion sync test
python tests/test_notion_sync.py

# Setup/validate Notion database
python tests/setup_notion_db.py

# Test Notion database properties
python -c "
from notion_integration import NotionIntegration
notion = NotionIntegration()
try:
    assignments = notion.get_all_assignments_from_notion()
    print(f'✅ Retrieved {len(assignments)} assignments from Notion')
except Exception as e:
    print(f'❌ Notion test failed: {e}')
"
```

### Email Parsing Tests

```bash
# Unit tests for parsing functions
python tests/test_parsing.py

# Test with real email data
python tests/test_real_parsing.py

# Test specific parsing patterns
python -c "
from moodle_fetcher import MoodleEmailFetcher
fetcher = MoodleEmailFetcher()

# Test with sample email
subject = 'Assignment ACTIVITY 1 - USER STORY has been changed'
body = 'Due: Friday, 5 September 2025, 10:09 AM'

result = fetcher._extract_assignment_info(subject, body)
print('✅ Parsing works' if result else '❌ Parsing failed')
print(f'Result: {result}')
"
```

### End-to-End Tests

```bash
# Full workflow test (no actual email sending)
python -c "
import json
from moodle_fetcher import MoodleEmailFetcher
from notion_integration import NotionIntegration

# Create test assignment
test_assignment = {
    'title': 'TEST ASSIGNMENT',
    'course': 'TEST COURSE',
    'due_date': '2025-08-15',
    'email_id': 'test_12345',
    'status': 'Pending'
}

# Test Notion sync
notion = NotionIntegration()
if notion.enabled:
    result = notion.sync_assignments([test_assignment])
    print(f'✅ E2E test: {result} assignment synced')
else:
    print('⚠️ Notion not enabled, skipping E2E test')
"
```

## 🏋️ Stress & Performance Tests

### Comprehensive Stress Testing

```bash
# Run full stress test suite
python tests/test_notion_stress.py

# Stress test with custom parameters
python -c "
from tests.test_notion_stress import main
import sys
success = main()
print('✅ All stress tests passed' if success else '❌ Some stress tests failed')
"
```

### Performance Benchmarks

```bash
# Measure parsing performance
python -c "
import time
from moodle_fetcher import MoodleEmailFetcher

fetcher = MoodleEmailFetcher()
subjects = ['Assignment TEST {i} has been changed'.format(i=i) for i in range(100)]

start = time.time()
for subject in subjects:
    fetcher._extract_assignment_info(subject, 'Due: 2025-08-15')
duration = time.time() - start

print(f'Parsed 100 subjects in {duration:.2f}s ({100/duration:.1f} subjects/sec)')
"

# Measure sync performance
python -c "
import time
import json
from notion_integration import NotionIntegration

# Generate test data
test_assignments = []
for i in range(10):
    test_assignments.append({
        'title': f'PERF TEST {i}',
        'email_id': f'perf_test_{i}_{int(time.time())}',
        'course': 'PERFORMANCE TEST',
        'due_date': '2025-08-15',
        'status': 'Pending'
    })

notion = NotionIntegration()
if notion.enabled:
    start = time.time()
    synced = notion.sync_assignments(test_assignments)
    duration = time.time() - start
    print(f'Synced {synced} assignments in {duration:.2f}s ({synced/duration:.1f} assignments/sec)')
else:
    print('Notion not enabled for performance test')
"
```

### Memory Usage Tests

```bash
# Monitor memory during operations
python -c "
import psutil
import os
from moodle_fetcher import MoodleEmailFetcher

process = psutil.Process(os.getpid())
start_memory = process.memory_info().rss / 1024 / 1024

fetcher = MoodleEmailFetcher()
# Simulate heavy parsing
for i in range(1000):
    fetcher._extract_assignment_info(f'Assignment TEST {i}', 'Due: 2025-08-15')

end_memory = process.memory_info().rss / 1024 / 1024
print(f'Memory usage: {start_memory:.1f}MB → {end_memory:.1f}MB (Δ{end_memory-start_memory:.1f}MB)')
"
```

## 🐛 Debugging Tools

### Log Analysis

```bash
# View recent errors
grep -i error logs/moodle_fetcher.log | tail -10

# View Notion-specific logs
grep -i notion logs/moodle_fetcher.log | tail -20

# View sync statistics
grep -E "(synced|assignments)" logs/moodle_fetcher.log | tail -15

# Real-time log monitoring
tail -f logs/moodle_fetcher.log
```

### Debug Mode Testing

```bash
# Enable debug logging for tests
export LOG_LEVEL=DEBUG

# Run tests with debug output
python tests/test_notion_sync.py

# Run fetcher with debug output
python run_fetcher.py --test --verbose

# Reset log level
unset LOG_LEVEL
```

### Data Validation Tools

```bash
# Validate assignments.json structure
python -c "
import json
import jsonschema

# Define expected schema
schema = {
    'type': 'array',
    'items': {
        'type': 'object',
        'required': ['title', 'email_id', 'course', 'due_date'],
        'properties': {
            'title': {'type': 'string'},
            'email_id': {'type': 'string'},
            'course': {'type': 'string'},
            'due_date': {'type': 'string'}
        }
    }
}

try:
    with open('data/assignments.json', 'r') as f:
        data = json.load(f)
    jsonschema.validate(data, schema)
    print(f'✅ assignments.json is valid ({len(data)} assignments)')
except Exception as e:
    print(f'❌ assignments.json validation failed: {e}')
"

# Check for duplicates
python -c "
import json
with open('data/assignments.json', 'r') as f:
    assignments = json.load(f)

email_ids = [a['email_id'] for a in assignments]
duplicates = [eid for eid in email_ids if email_ids.count(eid) > 1]

if duplicates:
    print(f'❌ Found {len(set(duplicates))} duplicate email IDs')
    for dup in set(duplicates):
        print(f'   {dup}')
else:
    print('✅ No duplicate email IDs found')
"
```

### Network & API Testing

```bash
# Test API endpoints manually
curl -X GET "https://api.notion.com/v1/databases/$NOTION_DATABASE_ID" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28"

# Test Todoist API
curl -X GET "https://api.todoist.com/rest/v2/projects" \
  -H "Authorization: Bearer $TODOIST_API_TOKEN"

# Test Gmail connection (requires app password)
python -c "
import imaplib
import os
from dotenv import load_dotenv
load_dotenv()

try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_PASSWORD'))
    print('✅ Gmail IMAP connection successful')
    mail.logout()
except Exception as e:
    print(f'❌ Gmail connection failed: {e}')
"
```

## 🛠️ Test Development

### Creating New Tests

```python
# Template for new test file
#!/usr/bin/env python3
"""
Test description here
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from your_module import YourClass

class TestYourFeature(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.some_method()
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
    
    def test_error_handling(self):
        """Test error handling."""
        with self.assertRaises(ValueError):
            self.instance.some_method(invalid_input=True)
    
    def tearDown(self):
        """Clean up after each test method."""
        pass

if __name__ == '__main__':
    unittest.main()
```

### Test Data Generation

```python
# Generate test assignments
def generate_test_assignment(index):
    from datetime import datetime, timedelta
    return {
        "title": f"TEST ASSIGNMENT {index}",
        "course": f"TEST COURSE {index}",
        "due_date": (datetime.now() + timedelta(days=index)).strftime('%Y-%m-%d'),
        "email_id": f"test_email_{index}_{int(time.time())}",
        "status": "Pending"
    }

# Generate batch of test data
test_assignments = [generate_test_assignment(i) for i in range(10)]
```

### Mock Testing

```python
# Mock external API calls for testing
import unittest.mock

def test_with_mocked_notion():
    with unittest.mock.patch('notion_integration.NotionIntegration.sync_assignments') as mock_sync:
        mock_sync.return_value = 5  # Mock successful sync of 5 assignments
        
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        result = notion.sync_assignments([])
        
        assert result == 5
        mock_sync.assert_called_once()
```

## 🚨 Troubleshooting Tests

### Common Test Failures

#### ❌ "ModuleNotFoundError"

**Cause:** Python path issues

**Solution:**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:/home/punisher/Documents/automate"

# Or run from project root
cd /home/punisher/Documents/automate
python tests/test_notion_sync.py
```

#### ❌ "Connection refused" / "Authentication failed"

**Cause:** Invalid credentials or network issues

**Solution:**
```bash
# Check .env file
cat .env

# Test basic connectivity
ping google.com

# Verify credentials manually
./deployment/run.sh test
```

#### ❌ "Database not found"

**Cause:** Notion database not shared with integration

**Solution:**
```bash
# Run database setup
python tests/setup_notion_db.py

# Check database permissions in Notion app
```

#### ❌ "Rate limit exceeded"

**Cause:** Too many API calls during testing

**Solution:**
```bash
# Wait and retry
sleep 60
python tests/test_notion_stress.py

# Reduce test batch sizes
```

### Test Environment Issues

```bash
# Clean test environment
rm -f data/assignments.json data/assignments.md

# Reset virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 📊 Test Reporting

### Generate Test Report

```bash
# Run tests with coverage
pip install coverage pytest
coverage run -m pytest tests/
coverage report
coverage html  # Generates htmlcov/index.html

# Run specific test with verbose output
python -m pytest tests/test_notion_sync.py -v -s

# Generate JSON report
python -m pytest tests/ --json-report --json-report-file=test_report.json
```

### Performance Benchmarking

```bash
# Benchmark all operations
python -c "
import time
import json
from moodle_fetcher import MoodleEmailFetcher
from notion_integration import NotionIntegration

print('🏃 Performance Benchmarks')
print('=' * 50)

# Email parsing benchmark
fetcher = MoodleEmailFetcher()
start = time.time()
for i in range(100):
    fetcher._extract_assignment_info(f'Assignment TEST {i}', 'Due: 2025-08-15')
parse_time = time.time() - start
print(f'Email parsing: {100/parse_time:.1f} emails/sec')

# Notion sync benchmark (if enabled)
notion = NotionIntegration()
if notion.enabled:
    test_data = [{'title': 'BENCH TEST', 'email_id': f'bench_{int(time.time())}'}]
    start = time.time()
    notion.sync_assignments(test_data)
    sync_time = time.time() - start
    print(f'Notion sync: {1/sync_time:.1f} assignments/sec')

print('✅ Benchmarking complete')
"
```

## 🎯 Continuous Testing

### Automated Test Scripts

```bash
#!/bin/bash
# daily_tests.sh - Run daily test suite

echo "🧪 Running Daily Test Suite"
echo "=========================="

# Basic connectivity tests
echo "📡 Testing connections..."
./deployment/run.sh test

# Unit tests
echo "🔬 Running unit tests..."
python tests/test_parsing.py

# Integration tests
echo "🔗 Running integration tests..."
python tests/test_notion_sync.py

# Performance check
echo "⚡ Performance check..."
python -c "
import time
from moodle_fetcher import MoodleEmailFetcher
start = time.time()
fetcher = MoodleEmailFetcher()
for i in range(50):
    fetcher._extract_assignment_info(f'Test {i}', 'Due: 2025-08-15')
duration = time.time() - start
print(f'Parsing performance: {50/duration:.1f} emails/sec')
if 50/duration < 100:
    print('⚠️ Performance below threshold')
else:
    print('✅ Performance OK')
"

echo "✅ Daily tests complete"
```

### Scheduled Testing

```bash
# Add to crontab for automated testing
# Run tests every day at 6 AM
0 6 * * * cd /home/punisher/Documents/automate && ./daily_tests.sh >> logs/test_results.log 2>&1

# Run stress tests weekly on Sunday at 3 AM
0 3 * * 0 cd /home/punisher/Documents/automate && python tests/test_notion_stress.py >> logs/stress_test.log 2>&1
```

## 📞 Support & Resources

### Quick Test Commands

```bash
# Emergency test suite (run when things break)
./deployment/run.sh test && python tests/test_parsing.py && echo "✅ Basic systems OK"

# Full system validation
python tests/setup_notion_db.py && python tests/test_notion_sync.py && echo "✅ Full system OK"

# Performance check
python tests/test_notion_stress.py
```

### Test File Quick Reference

| Test File | Purpose | Runtime | Command |
|-----------|---------|---------|---------|
| `setup_notion_db.py` | Database validation | 30s | `python tests/setup_notion_db.py` |
| `test_parsing.py` | Email parsing unit tests | 10s | `python tests/test_parsing.py` |
| `test_real_parsing.py` | Real email data tests | 60s | `python tests/test_real_parsing.py` |
| `test_notion_sync.py` | Notion integration tests | 45s | `python tests/test_notion_sync.py` |
| `test_notion_stress.py` | Performance & stress tests | 5-10min | `python tests/test_notion_stress.py` |

---

> 💡 **Pro Tip:** Run tests after every major change to catch issues early

> ⚡ **Quick Fix:** Most test failures are due to configuration issues - check `.env` file first

> 🔍 **Debug:** Use `--verbose` flag and check logs when tests fail

> 🏃 **Performance:** Regular stress testing helps identify bottlenecks before they become problems
