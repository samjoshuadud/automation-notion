#!/usr/bin/env python3
"""
Debug script to help identify the correct selectors for Google 2FA buttons
"""

import re

def analyze_html_for_buttons(html_content):
    """Analyze HTML content for potential button selectors"""
    print("🔍 Analyzing HTML for button elements...")
    
    # Look for elements containing resend-related text
    resend_patterns = [
        r'<[^>]*resend[^>]*>.*?</[^>]*>',
        r'<[^>]*>.*?resend.*?</[^>]*>',
        r'<span[^>]*>.*?Resend.*?</span>',
        r'<button[^>]*>.*?Resend.*?</button>',
        r'<a[^>]*>.*?Resend.*?</a>',
        r'<div[^>]*>.*?Resend.*?</div>'
    ]
    
    print("\n📤 RESEND BUTTON ANALYSIS:")
    found_resend = False
    for pattern in resend_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_resend = True
            print(f"✓ Found with pattern: {pattern}")
            for match in matches[:3]:  # Show first 3 matches
                print(f"  {match[:200]}...")
    
    if not found_resend:
        print("✗ No resend buttons found")
    
    # Look for elements containing "try another way" text
    try_another_patterns = [
        r'<[^>]*>.*?try another way.*?</[^>]*>',
        r'<[^>]*>.*?more ways.*?</[^>]*>',
        r'<span[^>]*>.*?Try another way.*?</span>',
        r'<button[^>]*>.*?Try another way.*?</button>',
        r'<a[^>]*>.*?Try another way.*?</a>',
        r'<div[^>]*>.*?Try another way.*?</div>'
    ]
    
    print("\n🔄 TRY ANOTHER WAY BUTTON ANALYSIS:")
    found_try_another = False
    for pattern in try_another_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_try_another = True
            print(f"✓ Found with pattern: {pattern}")
            for match in matches[:3]:  # Show first 3 matches
                print(f"  {match[:200]}...")
    
    if not found_try_another:
        print("✗ No 'try another way' buttons found")
    
    # Look for all clickable elements that might be buttons
    clickable_patterns = [
        r'<span[^>]*jsname[^>]*>.*?</span>',
        r'<div[^>]*role=["\']button["\'][^>]*>.*?</div>',
        r'<button[^>]*>.*?</button>',
        r'<a[^>]*href[^>]*>.*?</a>'
    ]
    
    print("\n🎯 ALL CLICKABLE ELEMENTS:")
    for pattern in clickable_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"\n📋 Pattern: {pattern}")
            for match in matches[:5]:  # Show first 5 matches
                # Clean up the match for display
                clean_match = re.sub(r'\s+', ' ', match).strip()
                print(f"  {clean_match[:150]}...")

if __name__ == "__main__":
    # Example usage - you can save page content to a file and analyze it
    print("To use this script:")
    print("1. When buttons don't work, save the page content to a file")
    print("2. Run: python debug_buttons.py < page_content.html")
    print("3. Or modify this script to read from a specific file")
    
    # For testing, you could read from stdin or a file
    try:
        import sys
        if not sys.stdin.isatty():
            html_content = sys.stdin.read()
            analyze_html_for_buttons(html_content)
    except:
        pass
