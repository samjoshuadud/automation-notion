# 🔍 Logic Errors, Loopholes & Bug Detection Guide

## Critical Areas to Check for Logic Errors & Loopholes

### 1. **Date & Time Logic Issues**

#### Common Date Bugs:
```python
# Test these edge cases:
invalid_dates = [
    "",                # Empty string
    "2025-02-29",     # Invalid leap year
    "2025-13-01",     # Invalid month  
    "2025-01-32",     # Invalid day
    "invalid-date",   # Malformed
    None,             # None value
]

# Past dates that could break reminder logic:
past_dates = [
    "2024-01-01",     # Far in past
    "2025-08-06",     # Yesterday
    str(datetime.now().date())  # Today
]
```

#### Potential Issues:
- ❌ **Reminder dates in the past** - Could create impossible reminders
- ❌ **Timezone handling** - No timezone awareness could cause issues
- ❌ **Leap year edge cases** - Feb 29 in non-leap years
- ❌ **Date format inconsistencies** - Different date formats could break parsing

### 2. **Duplicate Detection Loopholes**

#### Ways to Bypass Duplicate Detection:
```python
# These could create duplicates:
bypass_attempts = [
    {"title": "HCI - Activity 1 (User Story)", "email_id": "123"},
    {"title": "HCI - Activity 1 (User Stories)", "email_id": "123"},  # Plural vs singular
    {"title": "hci - activity 1 (user story)", "email_id": "123"},   # Case changes
    {"title": "HCI-Activity 1 (User Story)", "email_id": "123"},     # Spacing changes
    {"title": "HCI - Activity 1(User Story)", "email_id": "123"},    # Missing space
]
```

#### Potential Issues:
- ❌ **Case sensitivity bypass** - "HCI" vs "hci"
- ❌ **Punctuation changes** - "Activity 1" vs "Activity1"
- ❌ **Fuzzy matching too strict/loose** - Missing similar assignments
- ❌ **Email ID reuse** - Same email ID with different assignments

### 3. **Data Validation Gaps**

#### Malformed Data That Could Break System:
```python
dangerous_data = [
    None,                           # Null assignment
    {},                            # Empty assignment
    {"title": None},               # Null title
    {"title": ""},                 # Empty title
    {"email_id": ""},             # Empty email ID
    {"due_date": "invalid"},      # Invalid date
    {"course_code": None},        # Null course code
    {"raw_title": 123},           # Wrong data type
]
```

#### Potential Issues:
- ❌ **Type confusion** - Numbers instead of strings
- ❌ **Null pointer exceptions** - None values not handled
- ❌ **Empty string edge cases** - Empty strings treated as valid
- ❌ **SQL injection potential** - If data goes to database unsanitized

### 4. **API Rate Limiting & Error Handling**

#### Potential Issues:
- ❌ **Rate limit bypass** - Too many API calls too quickly
- ❌ **Network timeout handling** - Long requests could hang
- ❌ **401/403 error loops** - Invalid tokens causing infinite retries
- ❌ **Response parsing errors** - Malformed API responses

### 5. **Sync Logic Loopholes**

#### Race Conditions & Concurrency:
```python
# These scenarios could cause issues:
concurrent_scenarios = [
    "Two users syncing same assignment simultaneously",
    "Assignment updated while sync in progress", 
    "Todoist task deleted during status sync",
    "Network interruption during sync",
    "Large dataset sync causing memory issues"
]
```

#### Potential Issues:
- ❌ **Double creation** - Same task created twice
- ❌ **Status desync** - Local and Todoist out of sync
- ❌ **Memory leaks** - Large datasets not properly cleaned up
- ❌ **Partial sync failures** - Some assignments synced, others failed

## 🛠️ How to Test These Issues

### Automated Testing Commands:

```bash
# Run comprehensive bug detection
python tests/test_bug_detection.py

# Test logic validation 
python tests/test_logic_validation.py

# Test stress scenarios
python tests/test_stress.py

# Run master test suite
python tests/run_all_tests.py
```

### Manual Testing Scenarios:

#### 1. **Date Edge Cases**
```bash
# Test with assignments having invalid dates
python -c "
from todoist_integration import TodoistIntegration
todoist = TodoistIntegration()

# Test invalid dates
for date in ['2025-02-29', '2025-13-01', '', None]:
    reminder = todoist.calculate_reminder_date(str(date))
    print(f'Date: {date} → Reminder: {reminder}')
"
```

#### 2. **Malformed Data Handling**
```bash
# Test with malformed assignments
python -c "
from todoist_integration import TodoistIntegration
todoist = TodoistIntegration()

malformed = [{}, {'title': None}, {'title': ''}, None]
for assignment in malformed:
    try:
        if assignment is None:
            content = 'None assignment test'
        else:
            content = todoist.format_task_content(assignment)
        print(f'✅ Handled: {assignment}')
    except Exception as e:
        print(f'❌ Failed: {assignment} - {e}')
"
```

#### 3. **Duplicate Detection Bypass Tests**
```bash
# Test duplicate detection with similar data
python tests/test_duplicate_bypass.py
```

#### 4. **API Error Simulation**
```bash
# Test with invalid API token
TODOIST_TOKEN=invalid_token python run_fetcher.py --todoist --test
```

#### 5. **Large Dataset Testing**
```bash
# Test with many assignments
python tests/test_stress.py
```

## 🚨 Known Potential Issues Found

### Current Issues to Monitor:

1. **Date Validation Gap**: 
   - System accepts some invalid dates without proper validation
   - Potential fix: Add stricter date validation with try/catch

2. **Case Sensitivity in Duplicate Detection**:
   - Similar titles with different cases might not be detected as duplicates
   - Potential fix: Normalize all text before comparison

3. **API Token Validation**:
   - Invalid tokens don't always fail gracefully
   - Potential fix: Add explicit token validation on startup

4. **Memory Usage with Large Datasets**:
   - No limit on how many assignments can be processed at once
   - Potential fix: Add batch processing for large datasets

## 🔧 Recommended Fixes

### 1. Enhanced Date Validation
```python
def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False
```

### 2. Stronger Duplicate Detection
```python
def normalize_title(title):
    return re.sub(r'[^\w\s]', '', title.lower().strip())
```

### 3. API Error Handling
```python
def safe_api_call(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

### 4. Memory Management
```python
def batch_process(items, batch_size=100):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]
```

## 📋 Testing Checklist

- [ ] Invalid date handling
- [ ] Malformed assignment data  
- [ ] Duplicate detection bypasses
- [ ] API error scenarios
- [ ] Network interruption
- [ ] Large dataset performance
- [ ] Concurrent access
- [ ] Memory leak testing
- [ ] Rate limiting compliance
- [ ] Status sync accuracy

## 💡 Ongoing Monitoring

1. **Log Analysis**: Check `moodle_fetcher.log` for errors
2. **Performance Monitoring**: Track sync times and memory usage
3. **Data Integrity Checks**: Verify local vs Todoist data consistency
4. **User Reports**: Monitor for any duplicate tasks or missing assignments
