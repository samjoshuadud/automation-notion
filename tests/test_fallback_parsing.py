#!/usr/bin/env python3
"""
Test the enhanced email parsing with fallback patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moodle_fetcher import MoodleEmailFetcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_new_email_format():
    """Test parsing with the new email format from the attachment"""
    
    # Set up minimal environment for testing
    os.environ['GMAIL_EMAIL'] = 'test@example.com'
    os.environ['GMAIL_APP_PASSWORD'] = 'test_password'
    
    fetcher = MoodleEmailFetcher()
    
    # Test case from the email attachment
    subject = "Due on Friday, 8 August 2025, 11:59 PM: Midterm Assignment #1"
    body = """Hi CALEB JOSHUA,

The assignment Midterm Assignment #1 in course ELEC1 - ELECTIVE 1 (III-ACSAD) is due soon.

Due: Friday, 8 August 2025, 11:59 PM

Go to activity"""
    
    print("=" * 70)
    print("TESTING NEW EMAIL FORMAT WITH FALLBACK PATTERNS")
    print("=" * 70)
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("-" * 70)
    
    # Test the parsing
    result = fetcher._extract_assignment_info(subject, body)
    
    if result:
        print("✅ PARSING SUCCESSFUL!")
        print(f"   Title: {result.get('title')}")
        print(f"   Raw Title: {result.get('raw_title')}")
        print(f"   Due Date: {result.get('due_date')}")
        print(f"   Course: {result.get('course')}")
        print(f"   Course Code: {result.get('course_code')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Source: {result.get('source')}")
    else:
        print("❌ PARSING FAILED!")
    
    print("\n" + "=" * 70)
    
    # Test another case to make sure we didn't break existing functionality
    subject2 = "Assignment ACTIVITY 1 - USER STORY has been changed in the course HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)."
    body2 = """Assignment ACTIVITY 1 - USER STORY has been changed in the course HCI - HUMAN COMPUTER INTERACTION (III-ACSAD).

Due: Friday, 5 September 2025, 10:09 AM
Opens: Monday, 1 September 2025, 7:09 AM"""
    
    print("TESTING ORIGINAL FORMAT (should still work)")
    print("-" * 70)
    print(f"Subject: {subject2}")
    print(f"Body: {body2}")
    print("-" * 70)
    
    result2 = fetcher._extract_assignment_info(subject2, body2)
    
    if result2:
        print("✅ ORIGINAL FORMAT STILL WORKS!")
        print(f"   Title: {result2.get('title')}")
        print(f"   Raw Title: {result2.get('raw_title')}")
        print(f"   Due Date: {result2.get('due_date')}")
        print(f"   Course: {result2.get('course')}")
        print(f"   Course Code: {result2.get('course_code')}")
    else:
        print("❌ ORIGINAL FORMAT BROKEN!")

if __name__ == "__main__":
    test_new_email_format()
