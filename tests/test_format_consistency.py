#!/usr/bin/env python3
"""
Test script to verify that Notion and Todoist use the same formatting
"""

import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_integration import NotionIntegration
from todoist_integration import TodoistIntegration

def test_format_consistency():
    """Test that both integrations produce the same formatted titles"""
    
    # Test cases
    test_cases = [
        {
            'title': 'Activity 1 (User Story)',
            'course_code': 'ITEC101',
            'raw_title': 'ACTIVITY 1 - USER STORY [1]',
            'due_date': '2025-08-15',
            'course': 'Introduction to IT'
        },
        {
            'title': 'Assignment 2 (Database Design)',
            'course_code': 'DBMS201',
            'raw_title': 'ACTIVITY 2 - DATABASE DESIGN [2]',
            'due_date': '2025-08-20',
            'course': 'Database Management'
        },
        {
            'title': 'Final Project',
            'course_code': 'CS301',
            'raw_title': 'FINAL PROJECT SUBMISSION',
            'due_date': '2025-08-30',
            'course': 'Computer Science'
        }
    ]
    
    # Initialize integrations (will work even if credentials are missing)
    notion = NotionIntegration()
    todoist = TodoistIntegration()
    
    print("🔍 Testing format consistency between Notion and Todoist...")
    print("=" * 70)
    
    all_consistent = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"   Raw Title: {test_case.get('raw_title', 'N/A')}")
        print(f"   Course Code: {test_case.get('course_code', 'N/A')}")
        
        notion_formatted = notion.format_task_content(test_case)
        todoist_formatted = todoist.format_task_content(test_case)
        
        print(f"   Notion:  '{notion_formatted}'")
        print(f"   Todoist: '{todoist_formatted}'")
        
        is_consistent = notion_formatted == todoist_formatted
        print(f"   ✅ Consistent: {is_consistent}")
        
        if not is_consistent:
            all_consistent = False
            print("   ❌ MISMATCH DETECTED!")
    
    print("\n" + "=" * 70)
    if all_consistent:
        print("🎉 SUCCESS: All formatting is consistent between Notion and Todoist!")
        print("   Both platforms will now use the same titles for creation and deletion.")
    else:
        print("❌ FAILURE: Formatting inconsistencies detected!")
        print("   This may cause issues with cross-platform deletion.")
    
    return all_consistent

if __name__ == "__main__":
    test_format_consistency()
