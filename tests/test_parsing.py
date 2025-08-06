#!/usr/bin/env python3
"""
Test script to verify regex patterns work with the provided email example
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moodle_fetcher import MoodleEmailFetcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_parsing():
    """Test the email parsing with the provided email example"""
    
    # Sample email based on the provided example
    sample_subject = "Assignment ACTIVITY 1 - USER STORY has been changed in the course HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)."
    sample_body = """Assignment ACTIVITY 1 - USER STORY has been changed in the course HCI - HUMAN COMPUTER INTERACTION (III-ACSAD).

Change your notification preferences

Opens: Monday, 1 September 2025, 7:09 AM
Due: Friday, 5 September 2025, 10:09 AM

Are you reading this in an email? Download the mobile app and receive notifications on your mobile device."""
    
    print("=" * 60)
    print("TESTING EMAIL PARSING WITH SAMPLE EMAIL")
    print("=" * 60)
    
    print(f"Subject: {sample_subject}")
    print(f"Body: {sample_body}")
    print("-" * 60)
    
    # Create fetcher instance (we'll mock the credentials for testing)
    try:
        os.environ['GMAIL_EMAIL'] = 'test@example.com'
        os.environ['GMAIL_APP_PASSWORD'] = 'test_password'
        os.environ['SCHOOL_DOMAIN'] = 'umak.edu.ph'
        
        fetcher = MoodleEmailFetcher()
        
        # Test the parsing
        result = fetcher._extract_assignment_info(sample_subject, sample_body)
        
        if result:
            print("✅ EXTRACTION SUCCESSFUL!")
            print(f"Title (Display): {result.get('title')}")
            print(f"Title (Normalized): {result.get('title_normalized')}")
            print(f"Raw Title: {result.get('raw_title')}")
            print(f"Due Date: {result.get('due_date')}")
            print(f"Course: {result.get('course')}")
            print(f"Course Code: {result.get('course_code')}")
            print(f"Status: {result.get('status')}")
            print(f"Source: {result.get('source')}")
        else:
            print("❌ EXTRACTION FAILED!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("=" * 60)

def test_date_parsing():
    """Test various date formats"""
    
    print("TESTING DATE PARSING")
    print("-" * 30)
    
    os.environ['GMAIL_EMAIL'] = 'test@example.com'
    os.environ['GMAIL_APP_PASSWORD'] = 'test_password'
    
    fetcher = MoodleEmailFetcher()
    
    test_dates = [
        "Friday, 5 September 2025, 10:09 AM",
        "Monday, 1 September 2025, 7:09 AM",
        "5 September 2025",
        "September 5, 2025",
        "2025-09-05",
        "05/09/2025",
        "09/05/2025"
    ]
    
    for test_date in test_dates:
        result = fetcher._parse_date(test_date)
        print(f"'{test_date}' → '{result}'")

def test_title_formatting():
    """Test title formatting with proper capitalization"""
    
    print("\nTESTING TITLE FORMATTING")
    print("-" * 30)
    
    os.environ['GMAIL_EMAIL'] = 'test@example.com'
    os.environ['GMAIL_APP_PASSWORD'] = 'test_password'
    
    fetcher = MoodleEmailFetcher()
    
    test_cases = [
        ("ACTIVITY 1 - USER STORY", "HCI"),
        ("ACTIVITY 2 - WIREFRAMES", "HCI"),
        ("PROJECT 1 - DATABASE DESIGN", "DB"),
        ("ASSIGNMENT 3", "MATH"),
        ("Final Project", "CS")
    ]
    
    for title, course_code in test_cases:
        result = fetcher._format_assignment_title(title, course_code)
        print(f"'{title}' + '{course_code}':")
        print(f"  Display: '{result['display']}'")
        print(f"  Normalized: '{result['normalized']}'")
        print()

if __name__ == "__main__":
    test_email_parsing()
    test_date_parsing()
    test_title_formatting()
