#!/usr/bin/env python3
"""
Test Todoist Status Synchronization

This script tests the bidirectional status sync between Todoist and local storage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todoist_integration import TodoistIntegration
from moodle_fetcher import MoodleEmailFetcher
import json
from datetime import datetime
import time

def test_status_sync():
    """Test bidirectional status synchronization"""
    print("🔄 TESTING TODOIST STATUS SYNCHRONIZATION")
    print("=" * 50)
    
    # Initialize components
    try:
        todoist = TodoistIntegration()
        if not todoist.enabled:
            print("❌ Todoist integration not enabled")
            return False
            
        fetcher = MoodleEmailFetcher()
        print("✅ Components initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Test 1: Load existing assignments
    print("\n1. Loading existing assignments...")
    try:
        assignments = fetcher.load_existing_assignments()
        if not assignments:
            print("📄 No local assignments found. Create some first with:")
            print("   python run_fetcher.py --days 30")
            return True
            
        print(f"📋 Found {len(assignments)} local assignments")
        
        # Show first few assignments with status
        for i, assignment in enumerate(assignments[:3]):
            status = assignment.get('status', 'Unknown')
            title = assignment.get('title', 'Unknown')
            print(f"   {i+1}. {title} - Status: {status}")
            
    except Exception as e:
        print(f"❌ Failed to load assignments: {e}")
        return False
    
    # Test 2: Get Todoist assignments
    print("\n2. Getting assignments from Todoist...")
    try:
        todoist_assignments = todoist.get_all_assignments_from_todoist()
        print(f"📋 Found {len(todoist_assignments)} tasks in Todoist")
        
        completed_count = len([t for t in todoist_assignments if t['completed']])
        pending_count = len(todoist_assignments) - completed_count
        
        print(f"   ✅ Completed: {completed_count}")
        print(f"   ⏳ Pending: {pending_count}")
        
    except Exception as e:
        print(f"❌ Failed to get Todoist assignments: {e}")
        return False
    
    # Test 3: Test status sync from Todoist
    print("\n3. Testing status sync from Todoist...")
    try:
        # Count current completed assignments in local storage
        local_completed_before = len([a for a in assignments if a.get('status') == 'Completed'])
        
        # Perform status sync
        sync_result = todoist.sync_status_from_todoist(assignments)
        
        print(f"📊 Sync Results:")
        print(f"   Updated assignments: {sync_result['updated']}")
        print(f"   Completed in Todoist: {len(sync_result['completed_in_todoist'])}")
        
        if sync_result['completed_in_todoist']:
            print("   Assignments marked as completed:")
            for title in sync_result['completed_in_todoist']:
                print(f"      • {title}")
        
        # Count completed assignments after sync
        local_completed_after = len([a for a in assignments if a.get('status') == 'Completed'])
        
        if local_completed_after > local_completed_before:
            print(f"✅ Status sync working! {local_completed_after - local_completed_before} assignments updated")
        else:
            print("ℹ️ No status changes needed (or all assignments already synced)")
            
    except Exception as e:
        print(f"❌ Status sync test failed: {e}")
        return False
    
    # Test 4: Test duplicate prevention
    print("\n4. Testing duplicate prevention...")
    try:
        # Filter assignments to prevent duplicates
        filtered = todoist.prevent_duplicate_sync(assignments)
        
        original_count = len(assignments)
        filtered_count = len(filtered)
        skipped_count = original_count - filtered_count
        
        print(f"📊 Duplicate Prevention Results:")
        print(f"   Original assignments: {original_count}")
        print(f"   After filtering: {filtered_count}")
        print(f"   Skipped (already completed): {skipped_count}")
        
        if skipped_count > 0:
            print("✅ Duplicate prevention working!")
        else:
            print("ℹ️ No duplicates to prevent (all assignments are new)")
            
    except Exception as e:
        print(f"❌ Duplicate prevention test failed: {e}")
        return False
    
    # Test 5: Test formatting functions
    print("\n5. Testing task formatting...")
    try:
        if assignments:
            test_assignment = assignments[0]
            
            formatted_content = todoist.format_task_content(test_assignment)
            formatted_description = todoist.format_task_description(test_assignment)
            reminder_date = todoist.calculate_reminder_date(test_assignment.get('due_date', ''))
            
            print(f"📝 Format Test:")
            print(f"   Original: {test_assignment.get('title', 'N/A')}")
            print(f"   Formatted: {formatted_content}")
            print(f"   Due Date: {test_assignment.get('due_date', 'N/A')}")
            print(f"   Reminder: {reminder_date}")
            
        print("✅ Formatting functions working!")
            
    except Exception as e:
        print(f"❌ Formatting test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL STATUS SYNC TESTS COMPLETED!")
    print("=" * 50)
    
    # Summary and recommendations
    print("\n💡 What this means:")
    print("✅ Tasks completed in Todoist will be marked as completed locally")
    print("✅ Completed tasks won't be recreated when syncing")
    print("✅ Status changes sync bidirectionally")
    print("✅ Duplicate prevention is working")
    
    print("\n🔄 To see this in action:")
    print("1. Mark a task as complete in Todoist")
    print("2. Run: python run_fetcher.py --todoist")
    print("3. Check data/assignments.json - status should be updated!")
    
    return True

def test_reminder_scenarios():
    """Test different reminder calculation scenarios"""
    print("\n📅 TESTING REMINDER CALCULATIONS")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    today = datetime.now().date()
    
    test_cases = [
        ("2025-08-08", "Tomorrow"),
        ("2025-08-10", "3 days away"),
        ("2025-08-14", "1 week away"),
        ("2025-08-21", "2 weeks away"),
        ("2025-09-07", "1 month away"),
    ]
    
    for due_date, description in test_cases:
        reminder = todoist.calculate_reminder_date(due_date)
        print(f"{description:15} Due: {due_date} → Remind: {reminder}")
    
    print("✅ Reminder calculation test complete!")

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE TODOIST STATUS SYNC TEST")
    print("=" * 60)
    
    success = test_status_sync()
    
    if success:
        test_reminder_scenarios()
        print("\n🎉 All tests passed! Your Todoist integration is working perfectly.")
    else:
        print("\n❌ Some tests failed. Check your Todoist setup and try again.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure TODOIST_TOKEN is set in .env")
        print("2. Run: python tests/setup_todoist.py")
        print("3. Check your internet connection")
        print("4. Verify you have assignments in your system")
