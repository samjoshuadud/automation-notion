#!/usr/bin/env python3
"""
Test script to test Notion integration with a single assignment
"""

from notion_integration import NotionIntegration

def test_notion_sync():
    """Test Notion integration with a sample assignment"""
    
    print("🧪 Testing Notion integration...")
    print("=" * 40)
    
    # Initialize Notion integration
    notion = NotionIntegration()
    if not notion.enabled:
        print("❌ Notion integration not enabled")
        return False
    
    print("✅ Notion integration initialized")
    
    # Create a test assignment
    test_assignment = {
        'title': 'Test Assignment - Integration Test',
        'course': 'TEST101',
        'course_code': 'TEST',
        'status': 'Pending',
        'source': 'test',
        'due_date': '2025-08-20',
        'task_id': 'test_12345',
        'activity_type': 'Assignment'
    }
    
    print(f"📝 Testing with assignment: {test_assignment['title']}")
    
    # Check if assignment exists
    exists = notion.assignment_exists_in_notion(test_assignment)
    print(f"🔍 Assignment exists: {exists}")
    
    if not exists:
        # Try to create the assignment
        print("➕ Creating test assignment...")
        success = notion.create_assignment_page(test_assignment)
        if success:
            print("✅ Test assignment created successfully!")
        else:
            print("❌ Failed to create test assignment")
            return False
    else:
        print("ℹ️ Test assignment already exists")
    
    print("\n🎉 Notion integration test completed!")
    return True

if __name__ == "__main__":
    test_notion_sync()
