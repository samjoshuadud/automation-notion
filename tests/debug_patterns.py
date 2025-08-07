#!/usr/bin/env python3
"""
Debug the title extraction for the "Due on..." format
"""

import re

def debug_title_extraction():
    """Debug which patterns match"""
    
    subject = "Due on Friday, 8 August 2025, 11:59 PM: Midterm Assignment #1"
    body = """Hi CALEB JOSHUA,

The assignment Midterm Assignment #1 in course ELEC1 - ELECTIVE 1 (III-ACSAD) is due soon.

Due: Friday, 8 August 2025, 11:59 PM

Go to activity"""
    
    full_text = f"{subject}\n{body}"
    
    # Test patterns individually
    title_patterns = [
        r'Due\s+on\s+[^:]+:\s*(.+?)(?:\s*$)',
        r'Due\s+on\s+.*?:\s*(.+?)$',
        r'The\s+assignment\s+(.+?)\s+in\s+course',
        r'assignment\s+(.+?)\s+in\s+course',
        # Original patterns
        r'Assignment\s+([A-Z]+\s+\d+\s*-\s*[^h]+?)\s+has been\s+(?:changed|created|updated)',
        r'Assignment\s+(.+?)\s+has been\s+(?:changed|created|updated)',
    ]
    
    print("Testing title patterns:")
    print("=" * 60)
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("=" * 60)
    
    for i, pattern in enumerate(title_patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        try:
            match = re.search(pattern, subject, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                print(f"   ✅ Match in SUBJECT: '{result}'")
            else:
                match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1).strip()
                    print(f"   ✅ Match in FULL TEXT: '{result}'")
                else:
                    print(f"   ❌ No match")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    debug_title_extraction()
