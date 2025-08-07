#!/usr/bin/env python3
"""
Demo: Todoist Smart Reminder System

This script demonstrates how the smart reminder system works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from todoist_integration import TodoistIntegration

def demo_reminder_calculation():
    """Demonstrate the smart reminder calculation"""
    print("🧠 SMART REMINDER SYSTEM DEMO")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    today = datetime.now().date()
    
    # Test different scenarios
    test_scenarios = [
        (1, "Tomorrow"),
        (3, "3 days away"), 
        (5, "5 days away"),
        (7, "1 week away"),
        (10, "10 days away"),
        (14, "2 weeks away"),
        (21, "3 weeks away"),
        (30, "1 month away"),
        (60, "2 months away")
    ]
    
    print("📅 Reminder Schedule Examples:")
    print("-" * 50)
    print(f"{'Due In':<12} {'Due Date':<12} {'Remind On':<12} {'Days Before':<12}")
    print("-" * 50)
    
    for days_away, description in test_scenarios:
        due_date = (today + timedelta(days=days_away)).strftime('%Y-%m-%d')
        reminder_date = todoist.calculate_reminder_date(due_date)
        
        if reminder_date:
            reminder_dt = datetime.strptime(reminder_date, '%Y-%m-%d').date()
            days_before = (datetime.strptime(due_date, '%Y-%m-%d').date() - reminder_dt).days
            
            print(f"{description:<12} {due_date:<12} {reminder_date:<12} {days_before} days")
        else:
            print(f"{description:<12} {due_date:<12} {'N/A':<12} {'N/A':<12}")
    
    print("-" * 50)
    print("\n📋 Logic:")
    print("• 1-3 days away: Remind 1 day before")
    print("• 4-7 days away: Remind 3 days before") 
    print("• 8-14 days away: Remind 5 days before")
    print("• 15-30 days away: Remind 1 week before")
    print("• 30+ days away: Remind 2 weeks before")
    print("• Never reminds in the past (uses today if calculated reminder is past)")

def demo_task_formatting():
    """Demonstrate task formatting"""
    print("\n🎨 TASK FORMATTING DEMO")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    
    # Test different assignment formats
    test_assignments = [
        {
            "title": "HCI - Activity 1 (User Story [1])",
            "course_code": "HCI",
            "raw_title": "ACTIVITY 1 - USER STORY [1]",
            "due_date": "2025-09-05",
            "course": "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)",
            "email_id": "756"
        },
        {
            "title": "MATH - Activity 2 (Calculus Problems)",
            "course_code": "MATH",
            "raw_title": "ACTIVITY 2 - CALCULUS PROBLEMS [1]",
            "due_date": "2025-08-20", 
            "course": "MATHEMATICS 101",
            "email_id": "757"
        },
        {
            "title": "CS - Project 1 (Database Design)",
            "course_code": "CS",
            "raw_title": "PROJECT 1 - DATABASE DESIGN",
            "due_date": "2025-08-30",
            "course": "Computer Science - Database Systems",
            "email_id": "758"
        }
    ]
    
    for i, assignment in enumerate(test_assignments, 1):
        print(f"\nExample {i}:")
        print(f"Raw Title: {assignment['raw_title']}")
        
        formatted_content = todoist.format_task_content(assignment)
        formatted_description = todoist.format_task_description(assignment)
        reminder_date = todoist.calculate_reminder_date(assignment['due_date'])
        
        print(f"📝 Todoist Task: {formatted_content}")
        print(f"⏰ Reminder: {reminder_date}")
        print(f"📋 Description:")
        for line in formatted_description.split('\n'):
            print(f"   {line}")

if __name__ == "__main__":
    demo_reminder_calculation()
    demo_task_formatting()
    
    print("\n🎯 Ready to use!")
    print("Run: python run_fetcher.py --todoist")
    print("Check your Todoist 'School Assignments' project!")
