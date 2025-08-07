#!/usr/bin/env python3
"""
Quick test to verify Todoist duplicate detection logging
"""

import logging
import sys
import os

# Set up logging to see INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from todoist_integration import TodoistIntegration

def main():
    print("🎯 TODOIST DUPLICATE DETECTION TEST")
    print("=" * 50)
    
    # Initialize Todoist
    print("\n1. Initializing Todoist...")
    todoist = TodoistIntegration()
    
    if not todoist.enabled:
        print("❌ Todoist not enabled - check your TODOIST_TOKEN")
        return
    
    print("✅ Todoist initialized")
    
    # Test connection
    print("\n2. Testing connection...")
    if not todoist._test_connection():
        print("❌ Connection failed")
        return
    
    print("✅ Connection successful")
    
    # Get existing tasks
    print("\n3. Getting existing tasks...")
    existing_tasks = todoist.get_all_assignments_from_todoist()
    print(f"📋 Found {len(existing_tasks)} existing tasks")
    
    if existing_tasks:
        print("\nFirst few tasks:")
        for i, task in enumerate(existing_tasks[:3], 1):
            status = "✅ Completed" if task['completed'] else "⏳ Pending"
            print(f"   {i}. {status} - {task['title'][:60]}...")
    
    # Test duplicate detection
    print("\n4. Testing duplicate detection...")
    
    if existing_tasks:
        # Use the first existing task to test duplicate detection
        test_task = existing_tasks[0]
        
        # Create a similar assignment to test duplicate detection
        sample_assignment = {
            'title': test_task['title'],
            'title_normalized': test_task['title'].lower(),
            'email_id': test_task.get('email_id', 'test_123'),
            'course_code': 'TEST',
            'due_date': '2025-08-15',
            'course': 'Test Course',
            'source': 'Duplicate Test'
        }
        
        print(f"\n🔍 Testing with existing task: '{test_task['title'][:50]}...'")
        print("This should find a duplicate and show detailed logging...")
        
        # This should trigger the duplicate detection logging
        existing_id = todoist.task_exists_in_todoist(sample_assignment)
        
        if existing_id:
            print(f"✅ DUPLICATE FOUND! Task ID: {existing_id}")
            print("You should see detailed logging above showing the duplicate detection process")
        else:
            print("❌ No duplicate found - this might indicate an issue")
    else:
        print("No existing tasks to test with. Creating a test task first...")
        
        # Create a test assignment
        test_assignment = {
            'title': 'TEST - Activity 1 (Duplicate Detection Test)',
            'title_normalized': 'test - activity 1 (duplicate detection test)',
            'email_id': 'duplicate_test_123',
            'course_code': 'TEST',
            'due_date': '2025-08-15',
            'course': 'Test Course for Duplicate Detection',
            'source': 'Automated Test'
        }
        
        print("Creating test task...")
        if todoist.create_assignment_task(test_assignment):
            print("✅ Test task created")
            
            print("\n🔍 Now testing duplicate detection...")
            existing_id = todoist.task_exists_in_todoist(test_assignment)
            
            if existing_id:
                print(f"✅ DUPLICATE DETECTION WORKING! Found task ID: {existing_id}")
                print("Check the logs above to see the duplicate detection process")
            else:
                print("❌ Duplicate detection failed")
        else:
            print("❌ Failed to create test task")
    
    print("\n🎉 Test complete!")
    print("The duplicate detection logs should appear above with detailed information.")

if __name__ == "__main__":
    main()
