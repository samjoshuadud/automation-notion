#!/usr/bin/env python3
"""
Test script to verify the new reminder calculation logic
"""

import sys
import os
# Add parent directory to path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_integration import NotionIntegration
from todoist_integration import TodoistIntegration
from datetime import datetime, timedelta

def test_reminder_calculation():
    """Test the reminder calculation with different scenarios"""
    
    # Create integration instances (even if not fully configured, the methods should work)
    notion = NotionIntegration()
    todoist = TodoistIntegration()
    
    today = datetime.now().date()
    print(f"Today's date: {today}")
    print("=" * 60)
    
    # Test cases based on your requirements
    test_cases = [
        {
            "name": "Short assignment (4 days total, opens in 25 days, due in 29 days)",
            "opening_date": (today + timedelta(days=25)).strftime('%Y-%m-%d'),
            "due_date": (today + timedelta(days=29)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Medium assignment (7 days total, opens in 3 days, due in 10 days)",  
            "opening_date": (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            "due_date": (today + timedelta(days=10)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Already open assignment (due in 7 days)",
            "opening_date": (today - timedelta(days=2)).strftime('%Y-%m-%d'),
            "due_date": (today + timedelta(days=7)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Long assignment (opens tomorrow, due in 21 days)",
            "opening_date": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            "due_date": (today + timedelta(days=21)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Very short assignment (opens today, due in 3 days)",
            "opening_date": today.strftime('%Y-%m-%d'),
            "due_date": (today + timedelta(days=3)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Assignment without opening date (due in 14 days)",
            "opening_date": "No opening date",
            "due_date": (today + timedelta(days=14)).strftime('%Y-%m-%d'),
        },
        {
            "name": "Email date fallback: received 5 days ago, due in 10 days",
            "opening_date": "No opening date", 
            "due_date": (today + timedelta(days=10)).strftime('%Y-%m-%d'),
            "email_date": (today - timedelta(days=5)).strftime('Wed, %d %b %Y 15:34:53 +0000'),
        },
        {
            "name": "Email date fallback: received today, due tomorrow",
            "opening_date": "No opening date",
            "due_date": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            "email_date": today.strftime('Wed, %d %b %Y 10:00:00 +0000'),
        },
        {
            "name": "Email date fallback: received 20 days ago, due in 25 days",
            "opening_date": "No opening date",
            "due_date": (today + timedelta(days=25)).strftime('%Y-%m-%d'),
            "email_date": (today - timedelta(days=20)).strftime('Mon, %d %b %Y 09:15:30 +0000'),
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Opening: {test_case['opening_date']}")
        print(f"   Due: {test_case['due_date']}")
        if 'email_date' in test_case:
            print(f"   Email: {test_case['email_date']}")
        
        # Create test assignment
        assignment = {
            'title': f'Test Assignment {i}',
            'due_date': test_case['due_date'],
            'opening_date': test_case['opening_date']
        }
        
        # Add email date if present
        if 'email_date' in test_case:
            assignment['email_date'] = test_case['email_date']
        
        # Calculate reminders
        notion_reminder = notion.calculate_smart_reminder_date(assignment)
        todoist_reminder = todoist.calculate_reminder_date(assignment)
        
        print(f"   📅 Notion Reminder: {notion_reminder}")
        print(f"   📋 Todoist Reminder: {todoist_reminder}")
        
        # Analysis for Notion
        if notion_reminder:
            reminder_dt = datetime.strptime(notion_reminder, '%Y-%m-%d').date()
            days_until_reminder = (reminder_dt - today).days
            due_dt = datetime.strptime(test_case['due_date'], '%Y-%m-%d').date()
            days_until_due = (due_dt - today).days
            
            print(f"   ⏰ Notion: Reminder in {days_until_reminder} days ({days_until_due - days_until_reminder} days before due)")
            
            # Check if reminder respects opening date when available
            if test_case['opening_date'] != "No opening date":
                opening_dt = datetime.strptime(test_case['opening_date'], '%Y-%m-%d').date()
                if reminder_dt >= opening_dt:
                    print(f"   ✅ Notion: Reminder respects opening date")
                else:
                    print(f"   ❌ Notion: ERROR: Reminder before opening date!")
            
            # Check if reminder respects email date when no opening date
            elif 'email_date' in test_case:
                try:
                    email_dt = datetime.strptime(test_case['email_date'], '%a, %d %b %Y %H:%M:%S %z').date()
                    if reminder_dt >= email_dt:
                        print(f"   ✅ Notion: Reminder respects email date ({email_dt})")
                    else:
                        print(f"   ❌ Notion: ERROR: Reminder before email date!")
                except ValueError:
                    print(f"   ⚠️ Notion: Could not parse email date for validation")
        
        # Analysis for Todoist
        if todoist_reminder:
            reminder_dt = datetime.strptime(todoist_reminder, '%Y-%m-%d').date()
            days_until_reminder = (reminder_dt - today).days
            due_dt = datetime.strptime(test_case['due_date'], '%Y-%m-%d').date()
            days_until_due = (due_dt - today).days
            
            print(f"   ⏰ Todoist: Reminder in {days_until_reminder} days ({days_until_due - days_until_reminder} days before due)")
            
            # Check if reminder respects email date when no opening date
            if test_case['opening_date'] == "No opening date" and 'email_date' in test_case:
                try:
                    email_dt = datetime.strptime(test_case['email_date'], '%a, %d %b %Y %H:%M:%S %z').date()
                    if reminder_dt >= email_dt:
                        print(f"   ✅ Todoist: Reminder respects email date ({email_dt})")
                    else:
                        print(f"   ❌ Todoist: ERROR: Reminder before email date!")
                except ValueError:
                    print(f"   ⚠️ Todoist: Could not parse email date for validation")
        
        if not notion_reminder and not todoist_reminder:
            print(f"   ❌ No reminders set (assignment may be overdue or invalid)")
        
        print("-" * 80)

if __name__ == "__main__":
    test_reminder_calculation()
