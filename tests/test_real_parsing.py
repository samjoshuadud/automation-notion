#!/usr/bin/env python3
"""
Real-time test script that connects to Gmail and tests parsing on actual emails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moodle_fetcher import MoodleEmailFetcher
import logging
import json
from datetime import datetime

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_email_parsing():
    """Test parsing with real emails from Gmail"""
    
    print("=" * 80)
    print("REAL-TIME EMAIL PARSING TEST")
    print("Connecting to your actual Gmail account...")
    print("=" * 80)
    
    try:
        # Create fetcher instance with real credentials
        fetcher = MoodleEmailFetcher()
        
        # Connect to Gmail
        print("🔌 Connecting to Gmail...")
        mail = fetcher.connect_to_gmail()
        
        # Search for emails (last 7 days)
        print("🔍 Searching for Moodle emails...")
        email_ids = fetcher.search_moodle_emails(mail, days_back=7)
        
        print(f"📧 Found {len(email_ids)} emails to analyze")
        print("-" * 80)
        
        all_results = []
        hci_assignments = []
        
        # Process each email
        for i, email_id in enumerate(email_ids, 1):
            print(f"\n📨 Processing Email {i}/{len(email_ids)} (ID: {email_id.decode() if isinstance(email_id, bytes) else email_id})")
            print("-" * 40)
            
            try:
                # Get the raw email for debugging
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    import email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    subject = email_message['Subject'] or ""
                    body = fetcher._get_email_body(email_message)
                    
                    print(f"📋 Subject: {subject}")
                    print(f"📅 Date: {email_message['Date']}")
                    print(f"📝 Body preview: {body[:200]}...")
                    
                    # Parse the assignment info
                    assignment_info = fetcher._extract_assignment_info(subject, body)
                    
                    if assignment_info:
                        print(f"✅ PARSED SUCCESSFULLY:")
                        print(f"   Title (Display): {assignment_info.get('title')}")
                        print(f"   Title (Normalized): {assignment_info.get('title_normalized')}")
                        print(f"   Raw Title: {assignment_info.get('raw_title')}")
                        print(f"   Due Date: {assignment_info.get('due_date')}")
                        print(f"   Course: {assignment_info.get('course')}")
                        print(f"   Course Code: {assignment_info.get('course_code')}")
                        
                        # Add email ID for tracking
                        assignment_info['email_id'] = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                        assignment_info['email_subject'] = subject
                        assignment_info['email_date'] = email_message['Date']
                        
                        all_results.append(assignment_info)
                        
                        # Track HCI assignments specifically
                        if assignment_info.get('course_code') == 'HCI':
                            hci_assignments.append(assignment_info)
                    else:
                        print(f"❌ PARSING FAILED")
                        print(f"   Subject: {subject}")
                        print(f"   This email doesn't match our assignment patterns")
                
            except Exception as e:
                print(f"❌ Error processing email: {e}")
                continue
        
        # Summary
        print("\n" + "=" * 80)
        print("PARSING SUMMARY")
        print("=" * 80)
        print(f"📧 Total emails processed: {len(email_ids)}")
        print(f"✅ Successfully parsed: {len(all_results)}")
        print(f"🎯 HCI assignments found: {len(hci_assignments)}")
        
        # Show HCI assignments in detail
        if hci_assignments:
            print(f"\n📚 HCI ASSIGNMENTS BREAKDOWN:")
            print("-" * 50)
            for i, assignment in enumerate(hci_assignments, 1):
                print(f"{i}. {assignment.get('title')} (Due: {assignment.get('due_date')})")
                print(f"   Raw: {assignment.get('raw_title')}")
                print(f"   Email ID: {assignment.get('email_id')}")
                print()
        
        # Test duplicate detection
        print("\n🔍 TESTING DUPLICATE DETECTION:")
        print("-" * 50)
        
        # Load existing assignments
        existing_assignments = fetcher.load_existing_assignments()
        print(f"📄 Existing assignments in database: {len(existing_assignments)}")
        
        new_count = 0
        duplicate_count = 0
        
        for assignment in all_results:
            if fetcher.is_duplicate(assignment, existing_assignments):
                duplicate_count += 1
                print(f"⏭️  DUPLICATE: {assignment.get('title')}")
            else:
                new_count += 1
                print(f"✨ NEW: {assignment.get('title')}")
        
        print(f"\n📊 Results: {new_count} new, {duplicate_count} duplicates")
        
        # Save detailed results for analysis
        with open('real_email_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_emails': len(email_ids),
                'parsed_assignments': all_results,
                'hci_assignments': hci_assignments,
                'new_assignments': new_count,
                'duplicates': duplicate_count
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: real_email_test_results.json")
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ Error during real-time testing: {e}")
        import traceback
        traceback.print_exc()

def analyze_hci_patterns():
    """Analyze patterns in HCI emails specifically"""
    
    print("\n" + "=" * 80)
    print("HCI EMAIL PATTERN ANALYSIS")
    print("=" * 80)
    
    try:
        fetcher = MoodleEmailFetcher()
        mail = fetcher.connect_to_gmail()
        
        # Search specifically for HCI emails with broader criteria
        mail.select('inbox')
        
        # Search for emails containing "HCI" in the last 14 days
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        search_criteria = f'(FROM "noreply-tbl@umak.edu.ph" SINCE "{since_date}" BODY "HCI")'
        
        print(f"🔍 Searching with: {search_criteria}")
        
        status, message_ids = mail.search(None, search_criteria)
        if status == 'OK' and message_ids[0]:
            email_ids = message_ids[0].split()
            print(f"📧 Found {len(email_ids)} HCI-related emails")
            
            activity_patterns = {}
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status == 'OK':
                        import email
                        email_message = email.message_from_bytes(msg_data[0][1])
                        subject = email_message['Subject'] or ""
                        body = fetcher._get_email_body(email_message)
                        
                        print(f"\n📨 Subject: {subject}")
                        
                        # Look for activity patterns
                        import re
                        activity_matches = re.findall(r'ACTIVITY\s+(\d+)', subject + " " + body, re.IGNORECASE)
                        
                        for activity_num in activity_matches:
                            if activity_num not in activity_patterns:
                                activity_patterns[activity_num] = []
                            activity_patterns[activity_num].append({
                                'subject': subject,
                                'email_id': email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                            })
                
                except Exception as e:
                    print(f"Error processing email: {e}")
                    continue
            
            print(f"\n📊 ACTIVITY PATTERNS FOUND:")
            print("-" * 40)
            for activity_num in sorted(activity_patterns.keys()):
                print(f"Activity {activity_num}: {len(activity_patterns[activity_num])} emails")
                for item in activity_patterns[activity_num]:
                    print(f"  - {item['subject']}")
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ Error during pattern analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Choose test type:")
    print("1. Real-time email parsing test")
    print("2. HCI pattern analysis")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_real_email_parsing()
    elif choice == "2":
        analyze_hci_patterns()
    elif choice == "3":
        test_real_email_parsing()
        analyze_hci_patterns()
    else:
        print("Invalid choice. Running all tests...")
        test_real_email_parsing()
        analyze_hci_patterns()
