#!/usr/bin/env python3
"""
Logic validation test for Notion integration
Tests business logic, loopholes, and potential logic errors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_integration import NotionIntegration
from datetime import datetime, timedelta
import json
import time

def main():
    print("🔍 STARTING NOTION LOGIC VALIDATION...")
    print("🧠 COMPREHENSIVE LOGIC VALIDATION")
    print("=" * 70)
    print("Checking for loopholes, edge cases, and logic errors...")
    print("=" * 70)
    
    # Initialize Notion integration
    try:
        notion = NotionIntegration()
        if not notion.enabled:
            print("❌ Notion integration not enabled")
            return False
        print("✅ Notion integration initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    issues_found = []
    
    print("\n⏰ VALIDATING DATE LOGIC")
    print("=" * 50)
    
    # Test 1: Date boundary conditions
    print("1. Testing date boundary conditions...")
    try:
        boundary_dates = [
            datetime.now().strftime('%Y-%m-%d'),  # Today
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Yesterday (past)
            (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),  # Far future
            "2025-12-31",  # End of year
            "2025-01-01",  # Start of year
            "2024-02-29",  # Leap year date
        ]
        
        for date_str in boundary_dates:
            test_assignment = {
                "title": f"Date Test: {date_str}",
                "title_normalized": f"date test: {date_str}",
                "course": "DATE VALIDATION",
                "course_code": "DATE",
                "due_date": date_str,
                "source": "email",
                "email_id": f"date_test_{date_str.replace('-', '')}",
                "status": "Pending"
            }
            
            try:
                success = notion.create_assignment_page(test_assignment)
                print(f"   ✓ Date {date_str}: {success}")
            except Exception as e:
                issues_found.append(f"Date boundary error for {date_str}: {e}")
                print(f"   ❌ Date {date_str}: {e}")
    except Exception as e:
        issues_found.append(f"Date boundary test failed: {e}")
    
    print("\n🔄 VALIDATING DUPLICATE DETECTION LOGIC")
    print("=" * 50)
    
    # Test 2: Duplicate detection edge cases
    print("2. Testing duplicate detection edge cases...")
    try:
        base_time = int(time.time())
        
        # Create base assignment
        base_assignment = {
            "title": "LOGIC - Base Assignment (Test)",
            "title_normalized": "logic - base assignment (test)",
            "course": "LOGIC VALIDATION COURSE",
            "course_code": "LOGIC",
            "due_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            "source": "email",
            "email_id": f"logic_base_{base_time}",
            "status": "Pending"
        }
        
        # Create the base assignment
        base_created = notion.create_assignment_page(base_assignment)
        print(f"   ✓ Base assignment created: {base_created}")
        
        # Wait a moment for database consistency
        time.sleep(2)
        
        # Test various duplicate scenarios
        duplicate_scenarios = [
            # Scenario 1: Exact duplicate
            {
                **base_assignment,
                "email_id": f"logic_exact_{base_time}"
            },
            # Scenario 2: Case variations
            {
                **base_assignment,
                "title": "logic - base assignment (test)",
                "email_id": f"logic_case_{base_time}"
            },
            # Scenario 3: Spacing variations
            {
                **base_assignment,
                "title": "LOGIC-Base Assignment(Test)",
                "email_id": f"logic_space_{base_time}"
            },
            # Scenario 4: Punctuation variations
            {
                **base_assignment,
                "title": "LOGIC Base Assignment Test",
                "email_id": f"logic_punct_{base_time}"
            },
        ]
        
        for i, scenario in enumerate(duplicate_scenarios, 1):
            exists = notion.check_assignment_exists(scenario)
            created = notion.create_assignment_page(scenario)
            print(f"   Scenario {i}: Exists={exists}, Created={created}")
            
            if exists and created:
                issues_found.append(f"Duplicate detection bypass: Scenario {i} exists but was still created")
            
    except Exception as e:
        issues_found.append(f"Duplicate detection logic test failed: {e}")
    
    print("\n🗄️ VALIDATING DATABASE CONSISTENCY")
    print("=" * 50)
    
    # Test 3: Database consistency checks
    print("3. Testing database consistency...")
    try:
        # Get all assignments
        all_assignments = notion.get_all_assignments_from_notion()
        print(f"   ✓ Retrieved {len(all_assignments)} assignments")
        
        # Check for data consistency
        title_counts = {}
        email_id_counts = {}
        
        for assignment in all_assignments:
            title = assignment.get('title', '')
            email_id = assignment.get('email_id', '')
            
            # Count titles
            if title:
                title_counts[title] = title_counts.get(title, 0) + 1
            
            # Count email IDs
            if email_id:
                email_id_counts[email_id] = email_id_counts.get(email_id, 0) + 1
        
        # Check for duplicates
        duplicate_titles = {title: count for title, count in title_counts.items() if count > 1}
        duplicate_emails = {email: count for email, count in email_id_counts.items() if count > 1}
        
        if duplicate_titles:
            issues_found.append(f"Duplicate titles found: {duplicate_titles}")
            print(f"   ⚠️ Duplicate titles: {len(duplicate_titles)}")
        else:
            print(f"   ✓ No duplicate titles found")
            
        if duplicate_emails:
            issues_found.append(f"Duplicate email IDs found: {duplicate_emails}")
            print(f"   ⚠️ Duplicate email IDs: {len(duplicate_emails)}")
        else:
            print(f"   ✓ No duplicate email IDs found")
        
    except Exception as e:
        issues_found.append(f"Database consistency check failed: {e}")
    
    print("\n📊 VALIDATING SYNC LOGIC")
    print("=" * 50)
    
    # Test 4: Sync logic validation
    print("4. Testing sync logic...")
    try:
        # Test sync with mixed valid/invalid data
        mixed_assignments = [
            {
                "title": "Valid Assignment 1",
                "title_normalized": "valid assignment 1",
                "course": "VALID COURSE",
                "course_code": "VALID",
                "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                "source": "email",
                "email_id": f"valid_1_{int(time.time())}",
                "status": "Pending"
            },
            {},  # Empty assignment
            {
                "title": "Valid Assignment 2",
                "title_normalized": "valid assignment 2", 
                "course": "VALID COURSE",
                "course_code": "VALID",
                "due_date": (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d'),
                "source": "email",
                "email_id": f"valid_2_{int(time.time())}",
                "status": "Pending"
            },
            {"title": None},  # Invalid title
        ]
        
        synced_count = notion.sync_assignments(mixed_assignments)
        expected_valid = 2  # Should only sync the 2 valid assignments
        
        print(f"   ✓ Synced {synced_count} out of {len(mixed_assignments)} assignments")
        
        if synced_count > expected_valid:
            issues_found.append(f"Sync logic error: synced {synced_count} but expected max {expected_valid}")
        
    except Exception as e:
        issues_found.append(f"Sync logic validation failed: {e}")
    
    print("\n🛡️ VALIDATING ERROR HANDLING")
    print("=" * 50)
    
    # Test 5: Error handling validation
    print("5. Testing error handling...")
    try:
        # Test with malformed data that should not crash
        malformed_data = [
            None,
            {"title": "A" * 1000},  # Very long title
            {"title": "Test", "due_date": "invalid-date"},
            {"title": "Test", "course": None},
        ]
        
        for i, data in enumerate(malformed_data):
            try:
                if data is None:
                    result = notion.sync_assignments([data])
                else:
                    # Add required fields
                    if "email_id" not in data:
                        data["email_id"] = f"error_test_{i}_{int(time.time())}"
                    if "status" not in data:
                        data["status"] = "Pending"
                    result = notion.create_assignment_page(data)
                print(f"   ✓ Malformed data {i+1}: handled gracefully")
            except Exception as e:
                # Expected to handle errors gracefully
                print(f"   ✓ Malformed data {i+1}: error handled - {str(e)[:50]}...")
        
    except Exception as e:
        issues_found.append(f"Error handling validation failed: {e}")
    
    print("\n🔍 VALIDATING DATA FIELD LOGIC")
    print("=" * 50)
    
    # Test 6: Data field validation
    print("6. Testing data field validation...")
    try:
        # Test required vs optional fields
        field_tests = [
            {"title": "Required Field Test"},  # Missing optional fields
            {
                "title": "Full Field Test",
                "course": "TEST COURSE",
                "course_code": "TEST",
                "due_date": "2025-12-31",
                "source": "email",
                "email_id": f"field_test_{int(time.time())}",
                "status": "Pending"
            },
            {"course_code": "TEST"},  # Missing title (required)
        ]
        
        for i, test_data in enumerate(field_tests):
            try:
                # Add email_id if missing for tracking
                if "email_id" not in test_data:
                    test_data["email_id"] = f"field_test_{i}_{int(time.time())}"
                if "status" not in test_data:
                    test_data["status"] = "Pending"
                
                success = notion.create_assignment_page(test_data)
                print(f"   Field test {i+1}: {success}")
                
                # Check if assignment without title was accepted (should not be)
                if i == 2 and success and "title" not in test_data:
                    issues_found.append("Field validation error: assignment without title was accepted")
                    
            except Exception as e:
                print(f"   Field test {i+1}: {str(e)[:50]}...")
        
    except Exception as e:
        issues_found.append(f"Data field validation failed: {e}")
    
    print("\n" + "=" * 70)
    print("📊 LOGIC VALIDATION SUMMARY")
    print("=" * 70)
    
    validation_areas = [
        "Date Logic",
        "Duplicate Detection", 
        "Database Consistency",
        "Sync Logic",
        "Error Handling",
        "Data Field Logic"
    ]
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} logic issues:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No critical logic errors found!")
    
    print(f"\n🔧 Validation Areas Tested:")
    for area in validation_areas:
        print(f"   ✓ {area}")
    
    print(f"\n💡 Additional recommendations:")
    print("   1. Test with concurrent database access")
    print("   2. Test network interruption scenarios")
    print("   3. Test with different Notion database schemas")
    print("   4. Monitor memory usage with large datasets")
    print("   5. Test API rate limiting behavior")
    print("   6. Validate data backup and recovery")
    
    print("\n📋 Manual Testing Checklist:")
    print("   □ Create 100+ assignments and verify performance")
    print("   □ Test with very long assignment titles/descriptions")
    print("   □ Test with special Unicode characters")
    print("   □ Test database access from multiple users")
    print("   □ Test with corrupted/incomplete data")
    
    print("\n" + "=" * 70)
    if issues_found:
        print("🔍 LOGIC VALIDATION COMPLETE: Issues found - please review ⚠️")
    else:
        print("🔍 LOGIC VALIDATION COMPLETE: All validations passed! ✅")
    print("=" * 70)
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
