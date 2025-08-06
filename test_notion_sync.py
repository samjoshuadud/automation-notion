#!/usr/bin/env python3
"""
Test Notion integration with existing assignments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moodle_fetcher import MoodleEmailFetcher
from notion_integration import NotionIntegration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_notion_sync():
    """Test syncing existing assignments to Notion"""
    
    print("=" * 80)
    print("NOTION INTEGRATION TEST")
    print("Testing sync of existing assignments to Notion...")
    print("=" * 80)
    
    try:
        # Load existing assignments
        fetcher = MoodleEmailFetcher()
        assignments = fetcher.load_existing_assignments()
        
        print(f"📄 Found {len(assignments)} assignments in local database")
        
        # Show assignments that will be synced
        print("\n📚 ASSIGNMENTS TO SYNC:")
        print("-" * 50)
        for i, assignment in enumerate(assignments, 1):
            print(f"{i}. {assignment.get('title')}")
            print(f"   Due: {assignment.get('due_date')}")
            print(f"   Course: {assignment.get('course_code')}")
            print()
        
        # Initialize Notion integration
        print("🔌 Initializing Notion integration...")
        notion = NotionIntegration()
        
        if not notion.enabled:
            print("❌ Notion integration not enabled. Check your .env file.")
            return
        
        print("✅ Notion integration initialized successfully")
        
        # Test connection by trying to query the database
        print("\n🔍 Testing Notion database connection...")
        try:
            import requests
            url = f'https://api.notion.com/v1/databases/{notion.database_id}/query'
            headers = notion.headers
            response = requests.post(url, headers=headers, json={"page_size": 1})
            
            if response.status_code == 200:
                print("✅ Notion database connection successful")
                existing_pages = response.json().get('results', [])
                print(f"📊 Found {len(existing_pages)} existing entries in Notion database")
            else:
                print(f"❌ Notion database connection failed: {response.status_code}")
                print(f"Response: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error testing Notion connection: {e}")
            return
        
        # Sync assignments
        print(f"\n📝 Syncing {len(assignments)} assignments to Notion...")
        print("-" * 50)
        
        success_count = notion.sync_assignments(assignments)
        
        print(f"\n✅ Sync completed!")
        print(f"📊 Successfully synced: {success_count} assignments")
        print(f"🔗 Check your Notion database to see the results")
        
    except Exception as e:
        print(f"❌ Error during Notion sync test: {e}")
        import traceback
        traceback.print_exc()

def test_individual_assignment():
    """Test creating a single assignment in Notion"""
    
    print("\n" + "=" * 80)
    print("INDIVIDUAL ASSIGNMENT TEST")
    print("Testing creation of a single assignment...")
    print("=" * 80)
    
    try:
        # Create a test assignment
        test_assignment = {
            "title": "TEST - Activity 1 (Test Assignment)",
            "due_date": "2025-08-15",
            "course": "TEST - TEST COURSE (III-ACSAD)",
            "course_code": "TEST",
            "status": "Pending",
            "source": "test",
            "added_date": "2025-08-07 00:00:00"
        }
        
        print(f"🧪 Creating test assignment: {test_assignment['title']}")
        
        notion = NotionIntegration()
        if not notion.enabled:
            print("❌ Notion integration not enabled")
            return
        
        # Create the assignment
        success = notion.create_assignment_page(test_assignment)
        
        if success:
            print("✅ Test assignment created successfully!")
            print("🔗 Check your Notion database for the test entry")
        else:
            print("❌ Failed to create test assignment")
            
    except Exception as e:
        print(f"❌ Error during individual assignment test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Choose test type:")
    print("1. Sync all existing assignments to Notion")
    print("2. Create a single test assignment")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_notion_sync()
    elif choice == "2":
        test_individual_assignment()
    elif choice == "3":
        test_notion_sync()
        test_individual_assignment()
    else:
        print("Invalid choice. Running sync test...")
        test_notion_sync()
