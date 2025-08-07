#!/usr/bin/env python3
"""
Quick validation script to identify logic errors, loopholes, and bugs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todoist_integration import TodoistIntegration
from datetime import datetime, timedelta
import json

def main():
    print("🔍 QUICK LOGIC VALIDATION")
    print("=" * 50)
    
    # Initialize Todoist integration
    todoist = TodoistIntegration()
    
    issues_found = []
    
    print("\n1. Testing date logic loopholes...")
    # Test edge cases in date handling
    edge_dates = [
        "",  # Empty string
        "2025-02-29",  # Invalid date (not leap year)
        "2025-13-01",  # Invalid month
        "2025-01-32",  # Invalid day
        "invalid-date",  # Completely invalid
        "2024-02-29",  # Valid leap year date
        "2025-12-31",  # Valid end of year
    ]
    
    for date_str in edge_dates:
        try:
            reminder = todoist.calculate_reminder_date(date_str)
            print(f"   ✓ Date '{date_str}' → Reminder: {reminder}")
        except Exception as e:
            issues_found.append(f"Date handling error for '{date_str}': {e}")
            print(f"   ❌ Date '{date_str}' → Error: {e}")
    
    print("\n2. Testing assignment formatting loopholes...")
    # Test malformed assignment data
    malformed_data = [
        None,  # Completely None
        {},  # Empty dict
        {"title": None},  # None title
        {"title": ""},  # Empty title
        {"course_code": None},  # None course code
        {"due_date": "invalid"},  # Invalid due date
    ]
    
    for assignment in malformed_data:
        try:
            if assignment is None:
                content = todoist.format_task_content({})
            else:
                content = todoist.format_task_content(assignment)
            print(f"   ✓ Assignment {assignment} → Content: '{content[:30]}...'")
        except Exception as e:
            issues_found.append(f"Formatting error for {assignment}: {e}")
            print(f"   ❌ Assignment {assignment} → Error: {e}")
    
    print("\n3. Testing duplicate detection logic...")
    # Test potential duplicate detection bypasses
    similar_assignments = [
        {"title": "HCI - Activity 1 (User Story)", "email_id": "123"},
        {"title": "HCI - Activity 1 (User Stories)", "email_id": "124"},  # Similar but different
        {"title": "hci - activity 1 (user story)", "email_id": "125"},  # Case difference
        {"title": "HCI - Activity 1 (User Story)", "email_id": "123"},  # Exact duplicate
    ]
    
    for i, assignment in enumerate(similar_assignments):
        try:
            exists = todoist.task_exists_in_todoist(assignment)
            print(f"   Assignment {i+1}: exists={exists}")
        except Exception as e:
            issues_found.append(f"Duplicate detection error for assignment {i+1}: {e}")
            print(f"   ❌ Assignment {i+1} → Error: {e}")
    
    print("\n4. Testing sync logic edge cases...")
    # Test sync with problematic data
    sync_test_data = [
        [],  # Empty list
        [None],  # List with None
        [{}],  # List with empty dict
        [{"title": "Valid"}, None, {"title": "Another Valid"}],  # Mixed valid/invalid
    ]
    
    for i, data in enumerate(sync_test_data):
        try:
            count = todoist.sync_assignments(data)
            print(f"   Sync test {i+1}: synced {count} assignments")
        except Exception as e:
            issues_found.append(f"Sync error for test {i+1}: {e}")
            print(f"   ❌ Sync test {i+1} → Error: {e}")
    
    print("\n5. Testing status sync edge cases...")
    # Test status sync with problematic data
    status_test_data = [
        [],  # Empty list
        None,  # None input
        [{"title": "Test"}],  # Valid data
        [{"title": None}],  # Invalid title
        [{}],  # Empty assignment
    ]
    
    for i, data in enumerate(status_test_data):
        try:
            result = todoist.sync_status_from_todoist(data)
            print(f"   Status sync test {i+1}: {result}")
        except Exception as e:
            issues_found.append(f"Status sync error for test {i+1}: {e}")
            print(f"   ❌ Status sync test {i+1} → Error: {e}")
    
    print("\n6. Testing API error scenarios...")
    # Test with invalid token (temporarily)
    original_token = todoist.token
    todoist.token = "invalid_token_123"
    todoist.headers = {'Authorization': f'Bearer invalid_token_123'}
    
    try:
        connected = todoist.test_connection()
        if connected:
            issues_found.append("API validation: Invalid token should fail connection test")
            print("   ❌ Invalid token test failed - should not connect")
        else:
            print("   ✓ Invalid token correctly rejected")
    except Exception as e:
        print(f"   ✓ Invalid token handling: {e}")
    
    # Restore original token
    todoist.token = original_token
    todoist.headers = {'Authorization': f'Bearer {original_token}'}
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} issues:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No critical logic errors found!")
    
    print(f"\n💡 Additional recommendations:")
    print("   1. Test with large datasets (1000+ assignments)")
    print("   2. Test concurrent access scenarios")
    print("   3. Test network interruption during sync")
    print("   4. Monitor memory usage with large datasets")
    print("   5. Test database corruption recovery")
    print("   6. Validate rate limiting behavior")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
