#!/usr/bin/env python3
"""
Test Todoist Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from todoist_integration import TodoistIntegration
import json
from datetime import datetime

def test_todoist_integration():
    """Test Todoist integration functionality"""
    print("🧪 TESTING TODOIST INTEGRATION")
    print("=" * 40)
    
    # Initialize Todoist integration
    print("1. Initializing Todoist integration...")
    try:
        todoist = TodoistIntegration()
        if not todoist.enabled:
            print("❌ Todoist integration not enabled (check your TODOIST_TOKEN in .env)")
            return False
        print("✅ Todoist integration initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Todoist integration: {e}")
        return False
    
    # Test connection
    print("\n2. Testing Todoist API connection...")
    try:
        if todoist._test_connection():
            print("✅ Todoist API connection successful")
        else:
            print("❌ Todoist API connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Test project creation/retrieval
    print("\n3. Testing project creation/retrieval...")
    try:
        project_id = todoist.get_or_create_project("School Assignments")
        if project_id:
            print(f"✅ Project 'School Assignments' ready (ID: {project_id})")
        else:
            print("❌ Failed to get/create project")
            return False
    except Exception as e:
        print(f"❌ Project test failed: {e}")
        return False
    
    # Test task creation with sample assignment
    print("\n4. Testing task creation with new format...")
    sample_assignment = {
        "title": "HCI - Activity 1 (User Story [1])",
        "title_normalized": "hci - activity 1 (user story [1])",
        "due_date": "2025-08-15",
        "course": "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)",
        "course_code": "HCI",
        "status": "Pending",
        "source": "email",
        "raw_title": "ACTIVITY 1 - USER STORY [1]",
        "email_id": "test_001",
        "email_subject": "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD) content change",
        "email_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Test the formatting functions first
        formatted_content = todoist.format_task_content(sample_assignment)
        formatted_description = todoist.format_task_description(sample_assignment)
        reminder_date = todoist.calculate_reminder_date(sample_assignment['due_date'])
        
        print(f"📝 Formatted Content: {formatted_content}")
        print(f"📋 Description Preview: {formatted_description[:100]}...")
        print(f"⏰ Reminder Date: {reminder_date} (Due: {sample_assignment['due_date']})")
        
        success = todoist.create_assignment_task(sample_assignment, project_id)
        if success:
            print("✅ Test task created successfully with new format!")
        else:
            print("❌ Failed to create test task")
            return False
    except Exception as e:
        print(f"❌ Task creation test failed: {e}")
        return False
    
    # Test retrieving assignments from Todoist
    print("\n5. Testing assignment retrieval...")
    try:
        assignments = todoist.get_all_assignments_from_todoist()
        print(f"✅ Retrieved {len(assignments)} assignments from Todoist")
        
        # Show some details about the assignments
        if assignments:
            print("\nSample assignments in Todoist:")
            for i, assignment in enumerate(assignments[:3]):  # Show first 3
                print(f"  {i+1}. {assignment['title']}")
                if assignment['due_date']:
                    print(f"     Due: {assignment['due_date']}")
                print(f"     Status: {'Completed' if assignment['completed'] else 'Pending'}")
    except Exception as e:
        print(f"❌ Assignment retrieval test failed: {e}")
        return False
    
    # Test project statistics
    print("\n6. Testing project statistics...")
    try:
        stats = todoist.get_project_stats()
        if stats:
            print("✅ Project statistics retrieved:")
            print(f"  Total tasks: {stats.get('total_tasks', 0)}")
            print(f"  Completed: {stats.get('completed_tasks', 0)}")
            print(f"  Pending: {stats.get('pending_tasks', 0)}")
            print(f"  Overdue: {stats.get('overdue_tasks', 0)}")
            print(f"  Due today: {stats.get('due_today', 0)}")
            print(f"  Due this week: {stats.get('due_this_week', 0)}")
        else:
            print("⚠️ No statistics available")
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 ALL TODOIST INTEGRATION TESTS PASSED!")
    print("=" * 40)
    
    # Cleanup note
    print("\n📝 Note: The test task created above will remain in your Todoist.")
    print("   You can delete it manually if needed, or leave it as a test item.")
    
    return True

def test_sync_with_real_assignments():
    """Test syncing with real assignments from the system"""
    print("\n🔄 TESTING SYNC WITH REAL ASSIGNMENTS")
    print("=" * 40)
    
    # Load existing assignments if available
    try:
        with open('data/assignments.json', 'r') as f:
            assignments = json.load(f)
        
        if not assignments:
            print("📄 No assignments found in data/assignments.json")
            return True
            
        print(f"📋 Found {len(assignments)} assignments in local storage")
        
        # Initialize Todoist
        todoist = TodoistIntegration()
        if not todoist.enabled:
            print("❌ Todoist integration not enabled")
            return False
        
        # Sync first few assignments as test
        test_assignments = assignments[:3] if len(assignments) > 3 else assignments
        print(f"🧪 Testing sync with {len(test_assignments)} assignments...")
        
        synced_count = todoist.sync_assignments(test_assignments)
        print(f"✅ Successfully synced {synced_count} assignments to Todoist")
        
        return True
        
    except FileNotFoundError:
        print("📄 No assignments.json file found - this is normal for a fresh setup")
        return True
    except Exception as e:
        print(f"❌ Real assignment sync test failed: {e}")
        return False

if __name__ == "__main__":
    # Test basic Todoist integration
    success = test_todoist_integration()
    
    if success:
        # Test with real assignments if available
        test_sync_with_real_assignments()
    
    print("\n🏁 Todoist integration testing complete!")
    
    if success:
        print("\n💡 Next steps:")
        print("1. Add TODOIST_TOKEN to your .env file if not already done")
        print("2. Run: python run_fetcher.py --todoist")
        print("3. Check your Todoist for the 'School Assignments' project")
    else:
        print("\n🔧 Setup required:")
        print("1. Get your Todoist API token from: https://todoist.com/prefs/integrations")
        print("2. Add TODOIST_TOKEN=your_token_here to your .env file")
        print("3. Run this test again")
