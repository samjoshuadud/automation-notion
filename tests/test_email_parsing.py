#!/usr/bin/env python3
"""
Test the new email parsing logic for the "Due on..." format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moodle_fetcher import MoodleEmailFetcher

def test_new_email_format():
    """Test parsing of the new email format"""
    
    # Create a MoodleEmailFetcher instance (even if not fully configured, the parsing method should work)
    fetcher = MoodleEmailFetcher()
    
    # Test case based on the email image
    subject = "Due on Friday, 8 August 2025, 11:59 PM: Midterm Assignment #1"
    body = """Hi CALEB JOSHUA,

The assignment Midterm Assignment #1 in course ELEC1 - ELECTIVE 1 (III-ACSAD) is due soon.

Due: Friday, 8 August 2025, 11:59 PM

Go to activity"""
    
    print("Testing new email format parsing:")
    print("=" * 60)
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("=" * 60)
    
    # Test the parsing
    result = fetcher._extract_assignment_info(subject, body)
    
    if result:
        print("✅ Successfully parsed assignment:")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Raw Title: {result.get('raw_title', 'N/A')}")
        print(f"   Due Date: {result.get('due_date', 'N/A')}")
        print(f"   Opening Date: {result.get('opening_date', 'N/A')}")
        print(f"   Course: {result.get('course', 'N/A')}")
        print(f"   Course Code: {result.get('course_code', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Source: {result.get('source', 'N/A')}")
    else:
        print("❌ Failed to parse assignment")
    
    print("\n" + "=" * 60)
    
    # Test another case - original format for comparison
    subject2 = "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD) content change"
    body2 = """Assignment ACTIVITY 1 - USER STORY has been changed in the course HCI - HUMAN COMPUTER INTERACTION (III-ACSAD).

Change your notification preferences

Opens: Monday, 1 September 2025, 7:09 AM
Due: Friday, 5 September 2025, 10:09 AM

Are you reading this in an email? Download the mobile app and receive notifications on your mobile device."""
    
    print("Testing original email format parsing (for comparison):")
    print("=" * 60)
    print(f"Subject: {subject2}")
    print(f"Body: {body2}")
    print("=" * 60)
    
    result2 = fetcher._extract_assignment_info(subject2, body2)
    
    if result2:
        print("✅ Successfully parsed assignment:")
        print(f"   Title: {result2.get('title', 'N/A')}")
        print(f"   Raw Title: {result2.get('raw_title', 'N/A')}")
        print(f"   Due Date: {result2.get('due_date', 'N/A')}")
        print(f"   Opening Date: {result2.get('opening_date', 'N/A')}")
        print(f"   Course: {result2.get('course', 'N/A')}")
        print(f"   Course Code: {result2.get('course_code', 'N/A')}")
    else:
        print("❌ Failed to parse assignment")

if __name__ == "__main__":
    test_new_email_format()
