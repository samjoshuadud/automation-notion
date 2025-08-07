#!/usr/bin/env python3
"""
Quick validation script for both Todoist and Notion integrations
Tests basic functionality to identify critical issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_todoist():
    """Test basic Todoist functionality"""
    print("🔸 Testing Todoist Integration")
    print("-" * 40)
    
    try:
        from todoist_integration import TodoistIntegration
        todoist = TodoistIntegration()
        
        if not todoist.enabled:
            print("⚠️ Todoist not enabled (check credentials)")
            return False
        
        # Test connection
        connected = todoist._test_connection()
        if connected:
            print("✅ Todoist connection successful")
        else:
            print("❌ Todoist connection failed")
            return False
        
        # Test basic functionality
        test_assignment = {
            'title': 'Quick Test Assignment',
            'course_code': 'TEST',
            'due_date': '2025-08-15',
            'email_id': 'quick_test_123'
        }
        
        # Test formatting
        content = todoist.format_task_content(test_assignment)
        print(f"✅ Task formatting: {content[:30]}...")
        
        # Test date calculation
        reminder = todoist.calculate_reminder_date('2025-08-15')
        print(f"✅ Reminder calculation: {reminder}")
        
        return True
        
    except Exception as e:
        print(f"❌ Todoist test failed: {e}")
        return False

def test_notion():
    """Test basic Notion functionality"""
    print("\n🔸 Testing Notion Integration")
    print("-" * 40)
    
    try:
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        
        if not notion.enabled:
            print("⚠️ Notion not enabled (check credentials)")
            return False
        
        # Test connection
        connected = notion._test_connection()
        if connected:
            print("✅ Notion connection successful")
        else:
            print("❌ Notion connection failed")
            return False
        
        # Test database access
        assignments = notion.get_all_assignments_from_notion()
        print(f"✅ Database access: {len(assignments)} assignments found")
        
        return True
        
    except Exception as e:
        print(f"❌ Notion test failed: {e}")
        return False

def main():
    print("🚀 QUICK INTEGRATION VALIDATION")
    print("=" * 50)
    print("Testing basic functionality of both integrations...")
    print("=" * 50)
    
    todoist_ok = test_todoist()
    notion_ok = test_notion()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    print(f"Todoist Integration: {'✅ OK' if todoist_ok else '❌ ISSUES'}")
    print(f"Notion Integration:  {'✅ OK' if notion_ok else '❌ ISSUES'}")
    
    if todoist_ok and notion_ok:
        print("\n🎉 Both integrations working! Ready for full testing.")
    elif todoist_ok or notion_ok:
        print("\n⚠️ One integration has issues. Check credentials and setup.")
    else:
        print("\n❌ Both integrations have issues. Check setup and credentials.")
    
    print("\n💡 Next steps:")
    if todoist_ok:
        print("  • Run full Todoist tests: python tests/run_all_tests.py")
    if notion_ok:
        print("  • Run full Notion tests: python tests/run_notion_tests.py")
    if todoist_ok and notion_ok:
        print("  • Run comprehensive test suite: python tests/run_all_tests.py")
    
    return todoist_ok and notion_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
